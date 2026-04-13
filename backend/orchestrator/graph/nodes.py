import os
from pydantic import Field , BaseModel
from typing import Literal
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config.db import SessionLocal
from model.evidince_model import ChatState
from orchestrator.helper import execute_agent
from langchain_community.callbacks.manager import get_openai_callback


model = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
)

class RouterResponse(BaseModel):
    next_node: Literal["amazonvc_node", "summarize"]
    reasoning: str = Field(description="Explanation of why this node was chosen")
    direct_response: str = Field(
        default="", 
        description="If you can answer the user directly from findings or context without calling a node, provide the full answer here."
    )

# --- SETUP NODES ---
def extract_sku(state):
    db = SessionLocal()
    session_id = state["session_id"]
    chat_state = db.query(ChatState).filter_by(session_id=session_id).first()

    if not chat_state:
        chat_state = ChatState(session_id=session_id,history=[],findings=None)
        db.add(chat_state);db.commit()

    sku = chat_state.current_sku

    if not sku:
        with get_openai_callback() as cb:
            res = model.invoke(
                    f"""
                Extract ONLY the SKU from this text.

                Rules:
                - SKU is alphanumeric (e.g., B08SRDLYTR ,B08SRDLYTR)
                - Return ONLY the SKU
                - Do NOT return code
                - Do NOT explain
                - If no SKU found, return: None

                Text: {state['user_query']}
                """
            )
            print("---- SKU Extraction Tokens ----")
            print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
            print("--------------------------------")
        sku = res.content.strip().replace("`", "")
        if sku.lower() != "none":
            chat_state.current_sku = sku
            db.commit()
    history = list(chat_state.history or [])
    db.close()
    return {"sku": sku if sku and sku.lower() != "none" else None, "history": history}


# --- SUPERVISOR (The Decision Maker) ---
def supervisor_node(state):
    cases = state.get("cases", [])
    findings = state.get("findings", [])
    sku = state.get("sku")
    user_query = state.get("user_query", "").lower()
    iterations = state.get("iterations", 0)

    if iterations >= 3:
        return {"next_node": "summarize", "iterations": iterations + 1}
    
    #unsolved_anomalies = [c['anomaly_type'] for c in cases]
    solved_anomalies = [f.get('anomaly_type') for f in findings if isinstance(f, dict)]
    #remaining_db_tasks = [a for a in unsolved_anomalies if a not in solved_anomalies]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the Analysis Manager for SKU: {sku}.\n"
            "CURRENT CONTEXT:\n"
            #"- Anomalies found in DB: {remaining_tasks}\n"
            #"- Completed Analysis Findings: {solved_anomalies}\n"
            "- Raw Data/Findings: {findings}\n\n"
            "YOUR MISSION:\n"
            "1. If the user asks a general question (e.g., 'Hello', 'What can you do?') or the answer is already in the 'Raw Data/Findings', do NOT call a sub-agent.\n"
            "2. In such cases, set 'next_node' to 'summarize' and write your full answer in 'direct_response'.\n"
            "3. If specific analysis is still needed (e.g., checking PPM or traffic), choose 'amazonvc_node'.\n\n"
            "AVAILABLE NODES:\n"
            "- amazonvc_node: Use for Amazon Vendor Central data, PPM, or shipping issues.\n"
            "- summarize: Use if you are done or can answer now."
        )),
        ("human", "{user_query}")
    ])
    
    chain = prompt | model.with_structured_output(RouterResponse)
    
    with get_openai_callback() as cb:
        response = chain.invoke({
            "sku": sku, 
            #"remaining_tasks": remaining_db_tasks, 
            #"solved_anomalies": solved_anomalies,
            "findings": findings, # Pass the actual findings so it can read them
            "user_query": user_query
        })
    
    print(f"--- Supervisor Decision: {response.next_node} ---")
    
    # If the supervisor provided a direct answer, we store it in findings 
    # so the 'summarize' node can see it immediately.
    updates = {
        "next_node": response.next_node, 
        "iterations": iterations + 1
    }
    
    if response.direct_response:
        updates["findings"] = [{"direct_answer": response.direct_response}]
        
    return updates

# --- WORKER NODES (Sub-Agents) ---
def amazonvc_node(state):
    db = SessionLocal()
    sku = state["sku"]
    
    # The helper now just runs the one agent this node is responsible for
    finding = execute_agent(db, sku, "traffic")
    
    db.close()
    # Return as a list because GraphState findings uses operator.add
    return {"findings": [finding] if finding else []}


# --- SUMMARIZER ---
def summarize(state):
    findings_list = state.get("findings", [])
    
    # 1. Do the "heavy" LLM work FIRST without an active DB session
    direct_answer = next((f["direct_answer"] for f in findings_list if isinstance(f, dict) and "direct_answer" in f), None)
    
    if direct_answer:
        final_response = direct_answer
    else:
        findings_str = "\n".join([str(f) for f in findings_list])
        prompt = f"History: {state['history'][-2:]}\nQuery: {state['user_query']}\nFindings: {findings_str}\n\nSummarize the results."
        res = model.invoke(prompt)
        final_response = res.content

    # 2. NOW open the DB just to save and close immediately
    db = SessionLocal()
    try:
        chat_state = db.query(ChatState).filter_by(session_id=state["session_id"]).first()
        if chat_state:
            updated_hist = list(chat_state.history or [])
            updated_hist.append({"role": "user", "content": state["user_query"]})
            updated_hist.append({"role": "assistant", "content": final_response})
            chat_state.history = updated_hist
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
    finally:
        db.close()
    
    return {"user_query": final_response}