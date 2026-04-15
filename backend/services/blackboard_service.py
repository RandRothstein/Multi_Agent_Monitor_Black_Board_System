from config.db import SessionLocal
from model.evidince_model import Evidence,Case

class BlackboardService:
    # Static method don't have object states , we use static method to every time we call we require new connection
    @staticmethod
    def write_evidence(data: dict):
        with SessionLocal() as session:
            try:
                new_evidience = Evidence(
                product_id=data.get("product_id"),
                agent_name=data.get("agent_name"),

                anomaly_type=data.get("anomaly_type"),
                risk_score=data.get("risk_score"),

                # store full signals JSON
                signals=data.get("signals", []),

                finding_summary=data.get("finding_summary"),
                recommendation=data.get("recommendation"),
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

    
        