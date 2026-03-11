import os
from dotenv import load_dotenv
from sqlalchemy import text

from agents.base_agent import BaseAgent
from model.structured_output_model import StructuredOutput

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.manager import get_openai_callback
load_dotenv()

class TrafficAgent(BaseAgent):

    def __init__(self,db,sku_id):
        super().__init__(db,sku_id)

        self.llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0
        ).with_structured_output(StructuredOutput)

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

        result = self.db.execute(
            query,
            {'sku_id':self.sku_id}
        ).mappings().fetchall()


        if not result:
            return None
        
        prompt = f"""
        You are a traffic anomaly analysis agent.
        A traffic detector found abnormal traffic behavior.

        SKU DATA:
        {result}

        Tasks:
        1. Determine if traffic dropped significantly
        2. Estimate deviation severity
        3. Provide recommended action

        Return structured output.
        """
        with get_openai_callback() as cb:

            response = self.llm.invoke(prompt)
            print(f"---Traffic agent Token Usage")
            print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
            print(f"-------------------")

        # Return the dictionary version of the Pydantic model
        return response.model_dump()