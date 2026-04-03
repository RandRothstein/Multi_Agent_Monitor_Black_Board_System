from orchestrator.graph.workflow import build_graph


class SupervisorAgent:

    def __init__(self):
        self.app = build_graph()

    def analyze(self, user_query: str,session_id: str):
        
        inputs = {
            "session_id": session_id,
            "user_query": user_query,
            "sku": None,
            "cases": [],
            "findings": [],
            "history": []
        }
        
        # Execute the graph
        final_state = self.app.invoke(inputs)
        
        # Return the summary generated in the final node
        return {"summary": final_state["user_query"]}