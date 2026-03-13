from config.db import SessionLocal
from sqlalchemy import text
from orchestrator.helper import parse_sku_from_ai,run_cases
#from agents.conversion.price_agent import PriceAgent
from langchain.agents import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()
st.set_page_config(page_title='Solomon Council',layout='wide')

class SupervisorState(AgentState):
    sku_id : str
    anomaly_type : str
    sub_agent_name : str
    findings_summary : str

class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()
        st.title("🛡️ Solomon Council: Multi-Agent System")

        self.model = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0,
        )
    
    def user_interface(self):
        user_query = st.text_area("Ask your question about any product (e.g., 'Check status for SKU_123')",height = 100)
        if st.button('Analyze') and user_query:
            messages = [
                {"role": "user", "content": f"Extract the SKU ID from this query: {user_query}. Return ONLY the ID (e.g. SKU-002). If no ID is found, return 'None'."}
            ]
            response = self.model.invoke(messages)
            extracted_sku = parse_sku_from_ai(response)

            if extracted_sku and extracted_sku != None:

                query = text("""
                        SELECT TOP 1 sku_id,anomaly_type, severity
                    FROM dbo.[case] 
                    WHERE sku_id = :sku_id                        
                        """)
                cases = self.db.execute(query,{'sku_id':extracted_sku}).mappings().fetchall()
                if cases:
                    findings = run_cases(self.db,cases)   
                    self.display_results(findings)
                else:
                    st.warning(f"No anomalies found in the database for SKU: {extracted_sku}")
            else:
                st.error("Please Provide a valid SKU ID in you query.")

    def display_results(self, findings):
        if not findings:
            st.info("No anomalies were analyzed for this SKU.")
            return

        st.subheader("🛡️ Solomon Analysis Results")
        for finding in findings:
            st.write(f"**Agent:** {finding.get('agent_name')}")
            st.write(f"**Severity:** {finding.get('severity_score')}")
            st.markdown("### 📝 Findings & Recommendations")
            st.info(finding.get('finding_summary', "No detailed summary provided."))
    
    def close(self):
        self.db.close()