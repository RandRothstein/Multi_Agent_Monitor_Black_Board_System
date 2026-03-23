from agents.base_agent import BaseAgent
from sqlalchemy import text
from model.structured_output_model import StructuredOutput
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.manager import get_openai_callback
from dotenv import load_dotenv
import os

load_dotenv()

class PriceAgent(BaseAgent):


    def __init__(self,db,sku_id,history_context=""):
        super().__init__(db,sku_id)
        self.history_context = history_context
        self.llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0,
        ).with_structured_output(StructuredOutput)
        
    def run(self):
        query = text("""
        SELECT 
            p.sku_id,
            p.current_price,
            p.cost_price,
            p.min_margin_percent,
            c.competitor_name,
            c.competitor_price,
            c.is_out_of_stock as comp_oos
                        
            FROM dbo.sku_prices p
        LEFT JOIN dbo.competitor_prices c ON p.sku_id = c.sku_id
        WHERE p.sku_id = :sku_id
        """)

        result = self.db.execute(query,{'sku_id':self.sku_id}).mappings().fetchall()

        if not result:
                return None
        
        price_data = [dict(row) for row in result]

        prompt = f"""
        You are a Price Competitiveness Agent for {self.sku_id}. 
        TEAM HISTORY/PREVIOUS ACTIONS: {self.history_context}
        Your goal is to evaluate if our current price is causing a loss in market share or if we are leaving margin on the table.
        PRICING & COMPETITOR DATA:
        {price_data}

        Tasks:
        1. Calculate the Price Index (Our Price / Competitor Price).
        2. Check if our current margin is still above the 'min_margin_percent' threshold.
        3. Identify if we are 'Overpriced', 'Underpriced', or 'At Parity' compared to competitors.
        4. DO NOT suggest actions

        Return structured output.
        """
        with get_openai_callback() as cb:
                response = self.llm.invoke(prompt)
                print(f"---Price Competitiveness Agent Token Usage")
                print(f"Total Tokens: {cb.total_tokens}  |  Cost: ${cb.total_cost}")
                print(f"-------------------------------------------------")
    
        return response.model_dump()