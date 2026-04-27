import os, time, re
from pydantic import Field , BaseModel
from typing import Literal, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config.db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from model.evidince_model import ChatState
from orchestrator.helper import execute_agent, get_sku_action_history
from langchain_community.callbacks.manager import get_openai_callback
from sqlalchemy import select

model = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
)

# model = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",
#             google_api_key=os.getenv('GOOGLE_API_KEY'),
#             temperature=0,
# )

class RouterResponse(BaseModel):
    next_node: Literal["amazonvc_node", "summarize"]
    reasoning: str = Field(description="Explanation of why this node was chosen")
    direct_response: Optional[str] = Field(
        default=None,
        description="Provide the final answer here if you have enough info or if it's a general query."
    )
# --- SETUP NODES ---
async def extract_sku(state):
    """Detects SKU and pulls historical context. Caches result to avoid DB thrashing."""
    start = time.perf_counter()
    sku_pattern = r'\b[A-Z0-9]{8,12}\b'
    user_query = state.get('user_query', '').upper()
    session_id = state["session_id"]
    
    # 1. Return early if already in state
    if state.get("sku") and state.get("history_context"):
        return {"sku": state["sku"]}

    # 2. Regex Extraction
    regex_match = re.search(sku_pattern, user_query)
    sku = regex_match.group(0) if regex_match else None

    # 3. LLM Fallback
    if not sku:
        res = await model.ainvoke(f"Extract ONLY the Amazon SKU/ASIN from: {user_query}. Return 'None' if missing.")
        val = res.content.strip().replace("`", "")
        sku = val if val.lower() != "none" else None

    history_context = ""
    if sku:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ChatState).filter_by(session_id=session_id))
            chat_state = result.scalars().first()
            if not chat_state:
                chat_state = ChatState(session_id=session_id, history=[], current_sku=sku)
                db.add(chat_state)
            else:
                chat_state.current_sku = sku
            
            history_context = await get_sku_action_history(db, sku)
            await db.commit()

    print(f"Extract SKU time: {time.perf_counter() - start:.4f}s")
    return {"sku": sku, "history_context": history_context}

async def supervisor_node(state):
    """The Brain: Prevents redundant loops by checking the 'findings' list."""
    start = time.perf_counter()
    findings = state.get("findings", [])
    sku = state.get("sku")
    user_query = state.get("user_query", "")
    iterations = state.get("iterations", 0)
    history_context = state.get("history_context", "")

    # --- THE CIRCUIT BREAKER ---
    # Check if we already have actual data for this SKU in findings.
    # We look for 'finding_summary' or 'signals' which come from the Worker.
    has_actual_data = any("finding_summary" in f for f in findings if isinstance(f, dict))

    if has_actual_data or iterations >= 3:
        print("--- Supervisor: Data already found or max iterations reached. Routing to Summarize. ---")
        return {"next_node": "summarize", "iterations": iterations + 1}

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the Lead Amazon Vendor Central Analyst.\n"
            "SKU: {sku}\n"
            "CURRENT DATA: {findings}\n"
            "HISTORICAL CONTEXT: {history_context}\n\n"
            "GOAL: Answer the user query using data.\n"
            "RULES:\n"
            "1. If 'CURRENT DATA' is empty or missing metrics, route to 'amazonvc_node'.\n"
            "2. If 'CURRENT DATA' already contains a 'finding_summary', route to 'summarize'.\n"
            "3. Use 'direct_response' ONLY for status updates like 'I am checking the metrics for you.'\n"
            "4. Never route to 'amazonvc_node' more than once for the same issue."
        )),
        ("human", "{user_query}")
    ])

    chain = prompt | model.with_structured_output(RouterResponse)
    response = await chain.ainvoke({
        "sku": sku,
        "findings": findings,
        "user_query": user_query,
        "history_context": history_context
    })

    updates = {"next_node": response.next_node, "iterations": iterations + 1}
    if response.direct_response:
        updates["findings"] = [{"direct_answer": response.direct_response}]
    
    print(f"Supervisor time: {time.perf_counter() - start:.4f}s | Routing: {response.next_node}")
    return updates

async def amazonvc_node(state):
    """Worker: Fetches data. Ensures we return a list to satisfy state reducers."""
    sku = state["sku"]
    async with AsyncSessionLocal() as db:
        finding = await execute_agent(db, sku, "amazonvc_node")
    return {"findings": [finding] if finding else []}

async def summarize(state):
    """Final Output: Synthesizes findings and cleans up history."""
    start = time.perf_counter()
    findings_list = state.get("findings", [])
    user_query = state.get("user_query", "")

    # 1. Prioritization: Filter for the actual data from the worker
    real_data = [f for f in findings_list if isinstance(f, dict) and "finding_summary" in f]
    status_updates = [f.get("direct_answer") for f in findings_list if "direct_answer" in f]

    if real_data:
        # Use the latest actual data found
        latest_finding = real_data[-1].get("finding_summary", "")
        recommendation = real_data[-1].get("recommendation", "")
        
        prompt = (
            f"User Query: {user_query}\n"
            f"Technical Finding: {latest_finding}\n"
            f"Recommendation: {recommendation}\n\n"
            "Synthesize response to answer user query"
        )
        res = await model.ainvoke(prompt)
        final_response = res.content
    elif status_updates:
        # If no worker data exists, use the latest status update from the supervisor
        final_response = status_updates[-1]
    else:
        final_response = "I'm sorry, I couldn't retrieve the data for that SKU at this moment."

    # 2. Update History: Don't overwrite 'user_query' in the state!
    # Instead, we just prepare the history for the next turn.
    new_messages = [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": final_response}
    ]

    print(f"Summarization time: {time.perf_counter() - start:.4f}s")
    return {
        "final_report": final_response, # Use this key for your API response
        "history": new_messages
    }