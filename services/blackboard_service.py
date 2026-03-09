from config.db import SessionLocal
from model.evidince_model import Evidence

class BlackboardService:
    # Static method don't have object states , we use static method to every time we call we require new connection
    @staticmethod
    def write_evidence(data: dict):
        with SessionLocal() as session:
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