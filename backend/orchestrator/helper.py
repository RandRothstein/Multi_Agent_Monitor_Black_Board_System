from agents.traffic.amazonVC_agent import AmazonVCAgent
from services.blackboard_service import BlackboardService
from sqlalchemy import text
from functools import lru_cache

# Cache history for the duration of a single request to avoid repeated DB hits
@lru_cache(maxsize=32)
def get_sku_action_history(db_session, sku_id):
    """Utility to fetch the action history with optimized string joining."""
    history_query = text(
        "SELECT action_note FROM action_plans WHERE sku_id = :sku_id"
    )
    # Using scalars() is faster for single-column fetches in SQLAlchemy 2.0+
    result = db_session.execute(history_query, {'sku_id': sku_id})
    history = [row[0] for row in result if row[0]]
    
    return " ".join(history) if history else ""

# Map is defined outside the function to avoid re-instantiation on every call
AGENT_MAP = {
    "amazonvc_node": AmazonVCAgent,
    # Add future agents here
}

def execute_agent(db_session, sku_id, agent_type):
    """Executes a specific agent with minimized overhead."""
    
    agent_class = AGENT_MAP.get(agent_type)
    if not agent_class:
        return None

    # Fetch context (Cached if called multiple times in one loop)
    history_context = get_sku_action_history(db_session, sku_id)
    
    # Run agent
    agent = agent_class(db_session, sku_id, history_context)
    result = agent.run()

    if result:
        # Check if result is a list or dict before passing to evidence
        BlackboardService.write_evidence(result)
        
        # CRITICAL: Ensure result contains 'anomaly_type' so the 
        # Supervisor knows this task is finished.
        if isinstance(result, dict) and "anomaly_type" not in result:
            result["anomaly_type"] = agent_type
            
        return result
    
    return {"anomaly_type": agent_type, "status": "no_data_found"}