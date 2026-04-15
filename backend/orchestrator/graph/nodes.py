import os, time, re
from pydantic import Field , BaseModel
from typing import Literal, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config.db import SessionLocal
from model.evidince_model import ChatState
from orchestrator.helper import execute_agent, get_sku_action_history
from langchain_community.callbacks.manager import get_openai_callback


# model = ChatOllama(
#     model="qwen2.5:1.5b",
#     temperature=0,
# )

model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0,
)

class RouterResponse(BaseModel):
    next_node: Literal["amazonvc_node", "summarize"]
    reasoning: str = Field(description="Explanation of why this node was chosen")
    direct_response: Optional[str] = Field(
        default=None, 
        description="Provide the final answer here if you have enough info or if it's a general query."
    )

# --- SETUP NODES ---
def extract_sku(state):
    start = time.perf_counter()

    sku_pattern = r'\b[A-Z0-9]{8,12}\b'
    user_query = state.get('user_query', '').upper()
    regex_match = re.search(sku_pattern, user_query)

    db = SessionLocal()
    session_id = state["session_id"]

    chat_state = db.query(ChatState).filter_by(session_id=session_id).first()

    if not chat_state:
        chat_state = ChatState(
            session_id=session_id,
            history=[],
            findings=None
        )
        db.add(chat_state)
        db.commit()

    # ✅ ALWAYS define safely
    history = list(chat_state.history or [])
    history_context = ""

    sku = chat_state.current_sku

    if not sku:
        if regex_match:
            sku = regex_match.group(0)
        else:
            res = model.invoke(
                f"Extract ONLY the SKU from this text. If none, return 'None'. Text: {state['user_query']}"
            )
            sku = res.content.strip().replace("`", "")

        if sku and sku.lower() != "none":
            chat_state.current_sku = sku

            # only fetch context when valid SKU exists
            history_context = get_sku_action_history(db, sku)

            db.commit()

    db.close()

    end = time.perf_counter()
    print(f"Extract SKU execution time: {end - start:.4f} seconds")

    return {
        "sku": sku if sku and sku.lower() != "none" else None,
        "history": history,
        "history_context": history_context
    }

# --- SUPERVISOR (The Decision Maker) ---
def supervisor_node(state):
    start = time.perf_counter()
    findings = state.get("findings", [])
    sku = state.get("sku")
    user_query = state.get("user_query", "").lower()
    iterations = state.get("iterations", 0)
    history = state.get('history', [])[-2:]
    history_str = "\n".join([f"{h['role']}: {h['content']}" for h in history])
    history_context = state.get("history_context", "")

    # 1. Termination condition
    if iterations >= 3:
        return {"next_node": "summarize", "iterations": iterations + 1}
   
    # 2. Extract types of data already fetched to help the LLM decide
    solved_anomalies = [f.get('anomaly_type') for f in findings if isinstance(f, dict)]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the Lead Analyst for Amazon Vendor Central.\n"
            "CURRENT SKU: {sku}\n"
            "FINDINGS SO FAR: {findings}\n\n"
            f"ACTION HISTORY:\n{history_context}\n\n"
            f"History (last 2):\n{history_str}\n"
            "CHECKS ALREADY PERFORMED: {solved_anomalies}\n\n"
            "DECISION RULES:\n"
            "1. **Direct Answer**: If the query is a greeting ('Hi', 'Hello') or a general question NOT requiring data, set next_node='summarize' and provide 'direct_response'.\n"
            "2. **Check Findings**: If the 'FINDINGS SO FAR' already contains the data needed to answer the user's specific request, set next_node='summarize' and provide the final answer in 'direct_response'.\n"
            "3. **Call Worker**: ONLY if the query requires SKU-specific metrics (PPM, Traffic, Returns) that are NOT in the findings, set next_node='amazonvc_node'.\n"
            "4. **Prioritize efficiency**: Do not call workers if you can answer using the current context."
        )),
        ("human", "{user_query}")
    ])
    
    # Use the model with structured output
    chain = prompt | model.with_structured_output(RouterResponse)
    
    response = chain.invoke({
        "sku": sku, 
        "solved_anomalies": solved_anomalies,
        "findings": findings,
        "user_query": user_query
    })
    
    print(f"--- Supervisor: {response.reasoning} | Routing to: {response.next_node} ---")
    end = time.perf_counter()
    print(f"Supervisor time: {end - start:.4f} seconds")
    
    updates = {
        "next_node": response.next_node, 
        "iterations": iterations + 1
    }
    
    # If the supervisor found the answer, inject it into findings for the summarizer
    if response.direct_response:
        updates["findings"] = [{"direct_answer": response.direct_response}]
        
    return updates

# --- WORKER NODES (Sub-Agents) ---
def amazonvc_node(state):
    db = SessionLocal()
    sku = state["sku"]
    
    # The helper now just runs the one agent this node is responsible for
    finding = execute_agent(db, sku, "amazonvc_node")
    
    db.close()
    # Return as a list because GraphState findings uses operator.add
    return {"findings": [finding] if finding else []}


# --- SUMMARIZER ---
def summarize(state):
    """
    Summarize findings and persist result to DB once.
    Do heavy LLM work before opening DB to avoid long-lived sessions.
    """
    start = time.perf_counter()
    findings_list = state.get("findings", [])
    direct_answer = next((f.get("direct_answer") for f in findings_list if isinstance(f, dict) and "direct_answer" in f), None)

    if direct_answer:
        final_response = direct_answer
    else:
        findings_str = "\n".join([str(f) for f in findings_list])
        # Keep prompt short
        prompt = (
            f"History (last 2): {state.get('history', [])[-2:]}\n"
            f"Query: {state.get('user_query','')}\n"
            f"Findings: {findings_str}\n\nSummarize the results concisely."
            f"Perform the calculation to answer the user. Based on the requirements"
        )
        res = model.invoke(prompt)
        final_response = res.content

    # Persist the chat history and final response once (open DB only for that)
    db = state.get("db") or SessionLocal()
    try:
        chat_state = db.query(ChatState).filter_by(session_id=state["session_id"]).first()
        if chat_state:
            updated_hist = list(chat_state.history or [])
            updated_hist.append({"role": "user", "content": state.get("user_query")})
            updated_hist.append({"role": "assistant", "content": final_response})
            chat_state.history = updated_hist
            # Save findings as well (optional)
            chat_state.findings = state.get("findings", chat_state.findings)
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
    finally:
        if "db" not in state:
            db.close()
    end = time.perf_counter()
    print(f"Summarization time: {end - start:.4f} seconds")
    return {"user_query": final_response}