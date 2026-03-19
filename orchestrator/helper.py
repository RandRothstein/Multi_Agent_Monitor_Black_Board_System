from agents.traffic.traffic_agent import TrafficSourceAgent
from agents.conversion.price_agent import PriceAgent
from services.blackboard_service import BlackboardService
from sqlalchemy import text

def parse_sku_from_ai(ai_response):

    content = ai_response.content if hasattr(ai_response,'content') else str(ai_response)

    return content.strip()


def run_cases(db_session,cases):
    findings = []
    for case in cases:
        agents = []
        history_query = text("SELECT action_note FROM action_plans WHERE sku_id = :sku_id")
        history = db_session.execute(history_query, {'sku_id': case['sku_id']}).fetchall()
        history_context = " ".join([h[0] for h in history])
        if case.get('anomaly_type') == 'traffic_drop':
            agents = [
                TrafficSourceAgent(db_session,case['sku_id'],history_context)  
            ]
        if case.get('anomaly_type') == 'convertion_drop':
            agents =[
                PriceAgent(db_session,case['sku_id'],history_context)     
            ]

        print(agents)
        if not agents:
            continue
        
        for agent in agents:
            result = agent.run()

            if result:
                BlackboardService.write_evidence(result)
                findings.append(result)

    return findings