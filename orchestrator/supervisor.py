from config.db import SessionLocal
#from agents.conversion.price_agent import PriceAgent
from agents.traffic.traffic_agent import TrafficAgent
from services.blackboard_service import BlackboardService

class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()

    def run_cases(self, case):

        agents = []
        findings = []
        self.sku_id = case['sku_id']
        if case['anomaly_type'] =='traffic_drop':

            agents = [#PriceAgent(case)
                      TrafficAgent(self.db,case['sku_id'])  
                    ]
        for agent in agents:
            result = agent.run()

            if result:
                print(f"end: {result}")
                BlackboardService.write_evidence(result)
                findings.append(result)

        return findings

    def close(self):
        self.db.close()