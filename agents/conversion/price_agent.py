from agents.base_agent import BaseAgent
from sqlalchemy import text

class PriceAgent(BaseAgent):

    def run(self, product_id: int):

        query = text("""
            SELECT p.product_id,
                   p.current_price,
                   p.cost_price,
                   r.min_margin_percent
            FROM product_pricing p
            JOIN pricing_rules r ON p.category = r.category
            WHERE p.product_id = :product_id
        """)

        result = self.db.execute(query, {"product_id": product_id}).fetchone()

        if not result:
            return None

        margin = ((result.current_price - result.cost_price) / result.current_price) * 100

        if margin < result.min_margin_percent:
            severity = 0.9
            summary = f"Margin below threshold: {margin:.2f}%"

            return {
                "product_id": product_id,
                "agent_name": "PriceAgent",
                "metric_name": "margin_percent",
                "metric_value": margin,
                "severity_score": severity,
                "finding_summary": summary
            }

        return None