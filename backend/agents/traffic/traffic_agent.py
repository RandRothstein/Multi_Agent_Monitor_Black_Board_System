import os
from dotenv import load_dotenv
from sqlalchemy import text

from agents.base_agent import BaseAgent
from model.structured_output_model import StructuredOutput

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.manager import get_openai_callback
load_dotenv()

class TrafficSourceAgent(BaseAgent):

    def __init__(self,db,sku_id,history_context=""):
        super().__init__(db,sku_id)
        self.history_context = history_context
        self.llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0
        ).with_structured_output(StructuredOutput)

    def run(self):
        # Querying channel-level breakdown instead of totals
        query = text("""
            SELECT 
                source_name,
                current_sessions,
                previous_sessions
            FROM dbo.traffic_sources
            WHERE sku_id = :sku_id
        """)

        result = self.db.execute(
            query,
            {'sku_id': self.sku_id}
        ).mappings().fetchall()

        if not result:
            return None
        
        # Convert rows to a list of dicts for the LLM
        source_data = [dict(row) for row in result]
        
        prompt = f"""
        Analyze traffic for {self.sku_id}. 
        
        TEAM HISTORY/PREVIOUS ACTIONS: {self.history_context}
        CURRENT DATA: {source_data}

        TASKS:
        1. Identify the specific account (e.g. Target) and source causing the drop.
        2. If history shows a fix was made, evaluate if traffic is recovering.
        3. Determine if trend is improving or declining
        4. DO NOT suggest actions

        Return structured output.
        """
        
        with get_openai_callback() as cb:
            response = self.llm.invoke(prompt)
            print(f"--- Traffic Source Agent Token Usage ---")
            print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
            print(f"---------------------------------------")

        return response.model_dump()