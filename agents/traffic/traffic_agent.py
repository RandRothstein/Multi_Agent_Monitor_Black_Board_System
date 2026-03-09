from agents.base_agent import BaseAgent
from sqlalchemy import text
from config.db import SessionLocal

class TrafficAgent(BaseAgent):
    
    def run(self):
        query = text("""
            SELECT TOP 1 
                sku_id,
                retailer,
                sessions,
                baseline_sessions
            FROM dbo.sku_metrics
            WHERE sku_id = :sku_id
        """)

        result = self.db.execute(query, {"sku_id": self.sku_id}).mappings().fetchone()

        if not result or not result['baseline_sessions'] or result['baseline_sessions'] == 0:
            return None

        deviation = ((result['sessions'] - result['baseline_sessions']) 
                     / result['baseline_sessions']) * 100

        if deviation < -20:
            return {
                "product_id": self.sku_id,
                "agent_name": "TrafficAgent",
                "metric_name": "conversion_deviation",
                "metric_value": round(deviation, 2),
                "severity_score": 0.8,
                "finding_summary": f"Conversion dropped by {abs(deviation):.2f}%"
            }
        return None