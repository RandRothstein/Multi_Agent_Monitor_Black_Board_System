from agents.traffic.traffic_agent import TrafficSourceAgent
from agents.conversion.price_agent import PriceAgent
from services.blackboard_service import BlackboardService
from sqlalchemy import text

def get_sku_action_history(db_session, sku_id):
    """Utility to fetch the human/team action history for a SKU."""
    history_query = text(
        "SELECT action_note FROM action_plans WHERE sku_id = :sku_id"
    )
    history = db_session.execute(history_query, {'sku_id': sku_id}).fetchall()
    return " ".join([h[0] for h in history if h[0]])

def execute_agent(db_session, sku_id, agent_type):
    """
    Executes a specific agent. 
    This is called by the individual nodes in nodes.py.
    """
    history_context = get_sku_action_history(db_session, sku_id)
    
    # Map the node strings to actual Agent Classes
    agent_map = {
        "traffic": TrafficSourceAgent,
        #"rank": RankAgent,
        "price": PriceAgent,
        #"suppression": SuppressionAgent
    }
    
    agent_class = agent_map.get(agent_type)
    if not agent_class:
        return None

    # Instantiate and run
    agent = agent_class(db_session, sku_id, history_context)
    result = agent.run()

    if result:
        # Keep your Blackboard service for external logging/auditing
        BlackboardService.write_evidence(result)
        return result
    
    return None