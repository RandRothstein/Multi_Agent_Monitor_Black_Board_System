from agents.traffic.traffic_agent import TrafficAgent
from agents.conversion.price_agent import PriceAgent
from services.blackboard_service import BlackboardService


def parse_sku_from_ai(ai_response):

    content = ai_response.content if hasattr(ai_response,'content') else str(ai_response)

    return content.strip()


def run_cases(db_session,cases):
    findings = []

    for case in cases:
        agents = []
        if case.get('anomaly_type') == 'traffic_drop':
            agents = [
                TrafficAgent(db_session,case['sku_id'])  
            ]
        if case.get('anomaly_type') == 'convertion_drop':
            agents =[
                PriceAgent(db_session,case['sku_id'])     
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