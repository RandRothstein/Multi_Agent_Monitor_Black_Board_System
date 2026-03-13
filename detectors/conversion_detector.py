from config.db import SessionLocal
from sqlalchemy import text
from services.blackboard_service import BlackboardService

class ConversionDetector:

    async def detect(self):

        with SessionLocal() as session:
            query = """
            SELECT 
                sku_id,
                product_name,
                views,
                purchases,
                ROUND((purchases * 100.0 / views),2) as conversion_rate
            FROM product_performance
            """

            result = session.execute(text(query))

            rows = result.mappings().all()
            cases = []
            for row in rows:

                change = (row['purchases'] * 1.0 / row['views'])
                
                if change < 0.01:

                    case = {
                        "sku_id": row["sku_id"],
                        "retailer": row["product_name"],
                        "anomaly_type": "convertion_drop",
                        "severity": round(float(abs(row['conversion_rate'])), 2)

                    }
                    cases.append(case)

            if cases:
                for case in cases:
                    BlackboardService.write_case(case)

            return None