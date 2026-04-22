from config.db import AsyncSessionLocal
from model.evidince_model import Evidence, Case
from sqlalchemy.ext.asyncio import AsyncSession

class BlackboardService:
    @staticmethod
    async def write_evidence(db_session, data: dict): # Added db_session here
        try:
            new_evidence = Evidence(
                product_id=data.get("sku"),
                agent_name=data.get("agent_name", "AmazonVC"),
                anomaly_type=data.get("anomaly_type"),
                risk_score=data.get("data", {}).get("risk_score", 0),
                signals=data.get("data", {}).get("signals", []),
                finding_summary=data.get("data", {}).get("finding_summary"),
                recommendation=data.get("data", {}).get("recommendation")
            )
            db_session.add(new_evidence)
            await db_session.flush() # Use flush instead of commit to keep the transaction alive for the node
        except Exception as e:
            print(f"Error writing evidence: {e}")
            raise

    @staticmethod
    async def write_case(data: dict):
        async with AsyncSessionLocal() as session:
            try:
                new_case = Case(
                    sku_id=data['sku_id'],
                    retailer=data.get('retailer', 'Amazon'),
                    anomaly_type=data['anomaly_type'],
                    severity=float(data.get('severity', 0))
                )
                session.add(new_case)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise