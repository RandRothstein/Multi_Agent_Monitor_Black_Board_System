from sqlalchemy import text
from agents.traffic.amazonVC_agent import AmazonVCAgent
from services.blackboard_service import BlackboardService

async def get_sku_action_history(db_session, sku_id):
    history_query = text("SELECT action_note FROM action_plans WHERE sku_id = :sku_id")
    result = await db_session.execute(history_query, {'sku_id': sku_id})
    # Fixed scalar usage: result.scalars() gives the value directly
    history = [val for val in result.scalars() if val]
    return " ".join(history) if history else ""

AGENT_MAP = {
    "amazonvc_node": AmazonVCAgent,
}

async def execute_agent(db_session, sku_id, agent_type):
    agent_class = AGENT_MAP.get(agent_type)
    if not agent_class:
        return None
    
    agent = agent_class(db_session, sku_id)
    result = await agent.run()

    if result:
        await BlackboardService.write_evidence(db_session, result)   
        return result
    
    return {"anomaly_type": agent_type, "status": "no_data_found"}