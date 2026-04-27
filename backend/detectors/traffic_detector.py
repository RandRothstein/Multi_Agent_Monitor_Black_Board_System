from config.db import SessionLocal
from sqlalchemy import text
from services.blackboard_service import BlackboardService

class TrafficDetector:

    async def detect(self):

        with SessionLocal() as session:

            query = """
            SELECT
                sku_id,
                retailer,
                sessions,
                baseline_sessions
            FROM sku_metrics
            """

            result = session.execute(text(query))

            rows = result.mappings().all()
            cases = []
            for row in rows:
                if row["baseline_sessions"] == 0:
                    continue
                
                change = (
                    row["sessions"] - row["baseline_sessions"]
                ) / row["baseline_sessions"]

                if change < -0.30:

                    case = {
                        "sku_id": row["sku_id"],
                        "retailer": row["retailer"],
                        "anomaly_type": "traffic_drop",
                        "severity": round(float(abs(change)), 2)
                    }

                    cases.append(case)
            if cases:
                
                for case in cases:
                    BlackboardService.write_case(case)

        return None       