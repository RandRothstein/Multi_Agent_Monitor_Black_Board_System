import os
from sqlalchemy import text
from pydantic import Field , BaseModel
from typing import Literal
#from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config.db import SessionLocal
from model.evidince_model import ChatState
from orchestrator.helper import execute_agent
from langchain_community.callbacks.manager import get_openai_callback


model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0,
)

class RouterResponse(BaseModel):
    next_node: Literal["traffic_node", "price_node", "summarize"]
    reasoning: str = Field(description="Brief explanation of why this node was chosen")

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
                - SKU is alphanumeric (e.g., SKU123, ABC-123)
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

def fetch_cases(state):
    if not state["sku"]: return {"cases": []}
    db = SessionLocal()
    query = text("SELECT anomaly_type, severity FROM dbo.[case] WHERE sku_id = :sku")
    result = db.execute(query, {"sku": state["sku"]}).mappings().fetchall()
    db.close()
    return {"cases": [dict(r) for r in result]}

# --- SUPERVISOR (The Decision Maker) ---
def supervisor_node(state):
    cases = state.get("cases", [])
    findings = state.get("findings", [])
    sku = state.get("sku")
    user_query = state.get("user_query", "").lower()
    iterations = state.get("iterations", 0)

    if iterations >= 3: # Increased limit for more complex multi-step tasks
        return {"next_node": "summarize", "iterations": iterations + 1}
    
    # Track what we found in DB vs what we've already done
    unsolved_anomalies = [c['anomaly_type'] for c in cases]
    solved_anomalies = [f.get('anomaly_type') for f in findings if isinstance(f, dict)]
    remaining_db_tasks = [a for a in unsolved_anomalies if a not in solved_anomalies]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the Analysis Manager for SKU: {sku}.\n"
            "CURRENT CONTEXT:\n"
            "- Anomalies found in DB: {remaining_tasks}\n"
            "- Completed Analysis: {solved_anomalies}\n\n"
            "YOUR MISSION:\n"
            "1. Priority 1: If the user explicitly asks to run a specific check (e.g., 'Check market trends'), prioritize that even if not in DB.\n"
            "2. Priority 2: Investigate the DB anomalies listed above.\n"
            "3. Priority 3: If all tasks are done or user query is satisfied, choose 'summarize'.\n\n"
            "AVAILABLE NODES:\n"
            "- traffic_node: Use for traffic, clicks, or session drops.\n"
            "- price_node: Use for buy-box, pricing, or conversion issues.\n"
            "- market_node: Use for general market trends or competitor research.\n"
        )),
        ("human", "{user_query}")
    ])
    
    chain = prompt | model.with_structured_output(RouterResponse)
    with get_openai_callback() as cb:
        response = chain.invoke({
                "sku": sku, 
                "remaining_tasks": remaining_db_tasks, 
                "solved_anomalies": solved_anomalies,
                "user_query": user_query
            })
        print("---- Supervisor SubAgent Descision ----")
        print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
        print("--------------------------------")
    
    print(f"--- Supervisor Decision: {response.next_node} ---")
    return {"next_node": response.next_node, "iterations": iterations + 1}

# --- WORKER NODES (Sub-Agents) ---
def traffic_node(state):
    db = SessionLocal()
    sku = state["sku"]
    
    # The helper now just runs the one agent this node is responsible for
    finding = execute_agent(db, sku, "traffic")
    
    db.close()
    # Return as a list because GraphState findings uses operator.add
    return {"findings": [finding] if finding else []}

def price_node(state):
    db = SessionLocal()
    sku = state["sku"]
    
    finding = execute_agent(db, sku, "price")
    
    db.close()
    return {"findings": [finding] if finding else []}


# --- SUMMARIZER ---
def summarize(state):
    db = SessionLocal()
    findings = "\n".join([str(f) for f in state.get("findings", [])])
    prompt = f"History: {state['history'][-2:]}\nQuery: {state['user_query']}\nFindings: {findings}\n\nSummarize the results."
    with get_openai_callback() as cb:
        res = model.invoke(prompt)
        print("---- Summarization Tokens ----")
        print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
        print("-------------------------------")
    
    # Update DB History
    chat_state = db.query(ChatState).filter_by(session_id=state["session_id"]).first()
    if chat_state:
        updated_hist = list(chat_state.history or [])
        updated_hist.append({"role": "user", "content": state["user_query"]})
        updated_hist.append({"role": "assistant", "content": res.content})
        chat_state.history = updated_hist
        db.commit()
    db.close()
    return {"user_query": res.content} # Return final answer