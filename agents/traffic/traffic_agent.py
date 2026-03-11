import os
from dotenv import load_dotenv
from sqlalchemy import text

from agents.base_agent import BaseAgent
from model.structured_output_model import StructuredOutput

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI

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
        
        response = self.llm.invoke(prompt)
        structured = response["structured_response"]

        ai_message = response['messages'][1]  

        # Access the usage_metadata dictionary
        tokens = ai_message.usage_metadata

        print(f"Input Tokens: {tokens['input_tokens']}")
        print(f"Output Tokens: {tokens['output_tokens']}")
        print(f"Total: {tokens['total_tokens']}")

        return structured.model_dump()