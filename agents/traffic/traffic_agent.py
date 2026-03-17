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

    def __init__(self,db,sku_id):
        super().__init__(db,sku_id)

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
            ORDER BY current_sessions DESC
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
        You are a Traffic Source Analysis Agent.
        Your job is to identify which specific acquisition channel is causing a traffic anomaly.

        TRAFFIC SOURCE DATA:
        {source_data}

        Tasks:
        1. Identify the source with the largest percentage drop (e.g., Paid Search, Organic).
        2. Determine if the drop is isolated to one source or across all channels.
        3. Provide a recommendation (e.g., "Check Facebook Ad Campaign" or "Investigate SEO indexing").

        Return structured output.
        """
        
        with get_openai_callback() as cb:
            response = self.llm.invoke(prompt)
            print(f"--- Traffic Source Agent Token Usage ---")
            print(f"Total Tokens: {cb.total_tokens} | Cost: ${cb.total_cost}")
            print(f"---------------------------------------")

        return response.model_dump()