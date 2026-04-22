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

async def extract_sku(state):

    start = time.perf_counter()
    sku_pattern = r'\b[A-Z0-9]{8,12}\b'
    user_query = state.get('user_query', '').upper()
    regex_match = re.search(sku_pattern, user_query)
    session_id = state["session_id"]
    current_state_sku = state.get("sku",'')
    history_context = state.get("history_context",'')

    if current_state_sku and history_context:
        end = time.perf_counter()
        print(f"Extract SKU (cached) execution time: {end - start:.4f} seconds")
        return {"sku": current_state_sku, "history_context": history_context}  

    sku = None
    async with AsyncSessionLocal() as db:
        # 1. Fetch the state
        result = await db.execute(select(ChatState).filter_by(session_id=session_id))
        chat_state = result.scalars().first()
        # 2. Create if it doesn't exist

        if not chat_state:
            chat_state = ChatState(session_id=session_id, history=[], findings=None)
            db.add(chat_state)
            await db.commit()
            await db.refresh(chat_state)
        sku = chat_state.current_sku
        # 3. Logic to update SKU if missing (STILL INSIDE SESSION)

        if not sku:
            if regex_match:
                sku = regex_match.group(0)
            else:
                res = await model.ainvoke(f"Extract ONLY the SKU from this text. If none, return 'None'. Text: {user_query}")
                sku = res.content.strip().replace("`", "")
            if sku and sku.lower() != "none":
                chat_state.current_sku = sku
                # Fetch context and commit while session is open
                history_context = await get_sku_action_history(db, sku)

                await db.commit()
        
    end = time.perf_counter()
    print(f"Extract SKU execution time: {end - start:.4f} seconds")

    return {
        "sku": sku if sku and sku.lower() != "none" else None,
        "history_context": history_context
    }
# --- SUPERVISOR (The Decision Maker) ---

async def supervisor_node(state):
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
            "RULES:\n"
            "1. Understand the USER QUERY intent (issue / recommendation / explanation).Answering user query is the main GOAL.\n"
            "2. If findings already contain the answer → respond directly.\n"
            "3. If user asks for recommendation → use 'recommendation' field in findings.\n"
            "4. Do NOT repeat previous answers.\n"
            "5. If data missing → call amazonvc_node.\n"
            "6. Keep answer concise and specific.\n\n"

            "OUTPUT:\n"
            "- next_node: 'summarize' or 'amazonvc_node'\n"
            "- direct_response: final answer if available\n"
            "- reasoning: short justification"
        )),
        ("human", "{user_query}")
    ])
    # Use the model with structured output
    chain = prompt | model.with_structured_output(RouterResponse)
    response = await chain.ainvoke({
        "sku": sku,
        "solved_anomalies": solved_anomalies,
        "findings": findings,
        "user_query": user_query,
        "history_str": history_str
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

async def amazonvc_node(state):
    sku = state["sku"]
    # The helper now just runs the one agent this node is responsible f
    async with AsyncSessionLocal() as db:
        finding = await execute_agent(db, sku, "amazonvc_node")

    return {"findings": [finding] if finding else []}
# --- SUMMARIZER ---

async def summarize(state):

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
        res = await model.ainvoke(prompt)
        final_response = res.content
    new_messages = [
            {"role": "user", "content": state.get("user_query")},
            {"role": "assistant", "content": final_response}
        ]
    end = time.perf_counter()
    print(f"Summarization time: {end - start:.4f} seconds")
    return {
            "user_query": final_response,
            "history": new_messages
        }

