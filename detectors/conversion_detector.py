from config.db import SessionLocal
from sqlalchemy import text

class ConversionDetector:

    def detect(self):

        with SessionLocal() as session:
            query = """
            SELECT 
                sku_id,
                sales,
                profit
            FROM profit_margin
            """

            result = session.execute(text(query))

            rows = result.mappings().all()
            cases = []
            for row in rows:
                if row["baseline_sessions"] == 0:
                    continue

                change = ( (row['sales'] - row['profit']) / row['profit'])
                
                if change > 0.10:

                    case = {
                        "sku_id": row["sku_id"],
                        "retailer": row["retailer"],
                        "anomaly_type": "traffic_drop",
                        "severity": abs(change)

                    }
                    cases.append(case)

            return cases