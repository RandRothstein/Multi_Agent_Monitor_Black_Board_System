from agents.traffic.traffic_agent import TrafficAgent
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

        for agent in agents:
            result = agent.run()

            if result:
                BlackboardService.write_evidence(result)
                findings.append(result)

    return findings