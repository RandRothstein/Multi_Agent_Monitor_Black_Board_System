from config.db import SessionLocal
from sqlalchemy import text
from orchestrator.helper import parse_sku_from_ai, run_cases
from langchain_google_genai import ChatGoogleGenerativeAI
import os


class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()

        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0,
        )

    def analyze(self, user_query: str):
        try:
            # Step 1: Extract SKU
            messages = [{
                "role": "user",
                "content": f"Extract SKU ID from: {user_query}. Return only SKU or None."
            }]

            response = self.model.invoke(messages)
            sku = parse_sku_from_ai(response)

            if not sku or sku.lower() == "none":
                return {"error": "Invalid SKU"}

            # Step 2: Fetch cases
            query = text("""
                SELECT sku_id, anomaly_type, severity
                FROM dbo.[case]
                WHERE sku_id = :sku_id
            """)

            result = self.db.execute(query, {'sku_id': sku})
            cases = result.mappings().fetchall()

            # Step 3: Run agents
            findings = run_cases(self.db, cases) if cases else []

            # Step 4: Generate summary (LLM)
            summary_prompt = f"""
            User asked: {user_query}
            SKU: {sku}
            Findings: {findings}

            Provide a clear business summary.
            """

            summary = self.model.invoke(summary_prompt)

            return {
                "sku": sku,
                "summary": str(summary),
                "findings": findings
            }

        finally:
            self.db.close()