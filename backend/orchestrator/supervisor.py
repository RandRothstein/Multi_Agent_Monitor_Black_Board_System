from orchestrator.graph.workflow import build_graph
from langgraph.checkpoint.memory import MemorySaver

# Persistent memory and app to maintain state across the lifecycle of the server
shared_memory = MemorySaver()
shared_app = build_graph().compile(checkpointer=shared_memory,debug=True)

class SupervisorAgent:
    def __init__(self):
        self.app = shared_app

    async def analyze(self, user_query: str, session_id: str):
        inputs = {
            "session_id": session_id,
            "user_query": user_query,
            "history": [], 
            "findings": [],
            "iterations": 0
        }
        
        config = {"configurable": {"thread_id": session_id}}
        final_state = await self.app.ainvoke(inputs, config=config)
        
        return {
            "summary": final_state.get("final_report", "No report generated."),
            "sku": final_state.get("sku")
        }