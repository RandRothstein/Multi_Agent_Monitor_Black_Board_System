from config.db import SessionLocal
#from agents.conversion.price_agent import PriceAgent
from agents.traffic.traffic_agent import TrafficAgent
from services.blackboard_service import BlackboardService

from langchain.agents import create_agent,AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from detectors.traffic_detector import TrafficDetector
from model.evidince_model import Base
from config.db import engine
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()


class SupervisorState(AgentState):
    sku_id : str
    anomaly_type : str
    sub_agent_name : str
    findings_summary : str

class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()
        st.title("🛡️ Solomon Council: Multi-Agent System")
        st.set_page_config(page_title='Solomon Council',layout='wide')

        self.model = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0,
        )

    def parse_sku_from_ai(self, ai_response):

        content = ai_response.content if hasattr(ai_response,'content') else str(ai_response)

        return content.strip()
    
    def run_cases(self, case):
        agents = []
        findings = []
        self.sku_id = case['sku_id']
        if case['anomaly_type'] =='traffic_drop':

            agents = [#PriceAgent(case)
                      TrafficAgent(self.db,case['sku_id'])  
                    ]
        for agent in agents:
            result = agent.run()

            if result:
                #print(f"end: {result}")
                BlackboardService.write_evidence(result)
                findings.append(result)

        return findings
    
    def user_interface(self):
        user_query = st.text_area("Ask your question about any product (e.g., 'Check status for SKU_123')",height = 100)
        if st.button('Analyze') and user_query:
            messages = [
                {"role": "user", "content": f"Extract the SKU ID from this query: {user_query}. Return ONLY the ID (e.g. SKU-002). If no ID is found, return 'None'."}
            ]
            response = self.model.invoke(messages)
            extracted_sku = self.parse_sku_from_ai(response)

            if extracted_sku and extracted_sku != None:
                detector = TrafficDetector()
                cases = [c for c in detector.detect() if c['sku_id'] == extracted_sku]
            
                if cases:
                    all_findings = []
                    Base.metadata.create_all(bind=engine)
                    for case in cases:
                        findings = self.run_cases(case)
                        all_findings.extend(findings)

                    self.display_results(all_findings)

                else:
                    st.warning(f"No traffic anomalies found in the database for SKU: {extracted_sku}")
            else:
                st.error("Please Provide a valid SKU ID in you query.")

    def display_results(self, findings):
        if not findings:
            st.info("No anomalies were analyzed for this SKU.")
            return

        st.subheader("🛡️ Solomon Analysis Results")
        for finding in findings:
            # 'metric_name' comes from your StructuredOutput model
            with st.expander(f"Analysis: {finding.get('metric_name', 'Traffic Report')}", expanded=True):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    score = finding.get('severity_score', '0')
                    st.metric("Severity Score", f"{score}/1.0")
                    
                with col2:
                    st.write(f"**Agent:** {finding.get('agent_name')}")
                    st.write(f"**Metric Value:** {finding.get('metric_value')}")
                    st.markdown("### 📝 Findings & Recommendations")
                    # Since your model puts everything in finding_summary:
                    st.info(finding.get('finding_summary', "No detailed summary provided."))
    def close(self):
        self.db.close()