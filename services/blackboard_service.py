from config.db import SessionLocal
from model.evidince_model import Evidence,Case

class BlackboardService:
    # Static method don't have object states , we use static method to every time we call we require new connection
    @staticmethod
    def write_evidence(data: dict):
        with SessionLocal() as session:
            try:
                new_evidience = Evidence(
                    product_id=data["product_id"],
                    agent_name=data["agent_name"],
                    metric_name=data["metric_name"],
                    metric_value=data["metric_value"],
                    severity_score=data["severity_score"],
                    finding_summary=data["finding_summary"]
                )
                session.add(new_evidience)
                session.commit()
                
            except Exception as e:
                session.rollback()
                print("Error writing evidience:",e)
                raise
        
    @staticmethod
    def write_case(data: dict):
        with SessionLocal() as session:
            try:
                new_case = Case(
                    sku_id = data['sku_id'],
                    retailer = data['retailer'],
                    anomaly_type = data['anomaly_type'],
                    severity = float(data['severity'])
                )
                session.add(new_case)
                session.commit()


            except Exception as e:
                session.rollback()
                print("Error registering case",e)
                raise

    
        