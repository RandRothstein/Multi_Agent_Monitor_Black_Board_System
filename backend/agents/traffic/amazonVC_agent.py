from agents.base_agent import BaseAgent
from sqlalchemy import text
from model.structured_output_model import StructuredOutput
from langchain_community.callbacks.manager import get_openai_callback
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import time

load_dotenv()

class AmazonVCAgent(BaseAgent):

    def __init__(self,db,sku_id, history_context=""):

        super().__init__(db,sku_id)
        self.history_context = history_context
        self.llm =ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0,
).with_structured_output(StructuredOutput)

    def run(self):
        start = time.perf_counter()
        query = text("""
        SELECT top 1
            f.asin,
            f.shippedrevenue_amount as shipped_revenue,
            f.shippedcogs_amount as shipped_cogs,
            f.orderedunits as ordered_units,
            f.customerreturns,
            h.avg_rank_last_30_days as bsr_rank,
            h.in_stock
        FROM [AMZ].silver_amazon_vc_finance_accounting f
        LEFT JOIN [dbo].silver_mysamm_hist h ON f.asin = h.website_sku
        WHERE f.asin = :sku_id
        ORDER BY f.startdate DESC;
        """)

        result = self.db.execute(query, {'sku_id': self.sku_id}).mappings().fetchone()
        end = time.perf_counter()
        print(f"AmazonVC db time: {end - start:.4f} seconds")
        if not result:
            return None

        vc_data = dict(result)

        prompt = f"""
        Your the Amazon VC sub-agent in the SOL architecture for SKU_ID: {self.sku_id}.
        
        GOAL: Detect suppression, PPM risks, and operational compliance issues.
        
        AMAZON VC PERFORMANCE DATA:
        {vc_data}

        TASKS:
        1. Calculate Net PPM %: (Shipped Revenue - Shipped COGS) / Shipped Revenue.
        2. Evaluate Suppression Risk:
           - PPM < 32%: Generate a MEDIUM warning.
           - PPM 28-30%: Generate a HIGH alert (Critical suppression threshold).
        3. Monitor Operational Health:
           - Flag if 'in_stock' is false or if 'customerreturns' indicates a high-return trend.
        4. Identify Growth/Risk: 
           - Note BSR (Best Seller Rank) trends.
        5. DO NOT suggest actions (Actions are auto-drafted by the Action Agent).

        Return structured output identifying PPM status, risk level (LOW/MEDIUM/HIGH), and operational flags.
        """
        start = time.perf_counter()
        with get_openai_callback() as cb:
            response = self.llm.invoke(prompt)
            print(f"---Amazon VC Agent Token Usage")
            print(f"Total Tokens: {cb.total_tokens}  |  Cost: ${cb.total_cost}")
            print(f"-------------------------------------------------")
        end = time.perf_counter()
        print(f"AmazonVC agent end time: {end - start:.4f} seconds")
        return response.model_dump()        