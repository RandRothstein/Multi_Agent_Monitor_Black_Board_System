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

model = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    google_api_key = os.getenv('GOOGLE_API_KEY'),
    temperature = 0
)

agent = create_agent(
    model = model,
    tools = [],
    state_schema = SupervisorState,
    checkpointer = InMemorySaver()
)

class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()
        st.set_page_config(page_title='Solomon Council',layout='wide')
        st.title("Multi Agent System")

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
    
    def user_cases(self):
         user_query = st.text_area("Ask your question about any product",height = 100)
         if st.button('Analyze') and user_query:
            response = agent.invoke({'messages':[{'role':"user","content": f"Extract the SKU ID from this query: {user_query}"}]})
            extracted_sku = self.parse_sku_from_ai(response)

            if extracted_sku :
                detector = TrafficDetector()
                cases = [c for c in detector.detect() if c['sku_id'] == extracted_sku]
            else:
                st.write(f"Please provide SKU_ID to perform analysis")
            
            if cases:
                all_findings = []
                Base.metadata.create_all(bind=engine)
                for case in cases:
                    findings = self.run_cases(case)
                    all_findings.extend(findings)

            self.display_results(all_findings)

    def display_results(self, findings):
        st.subheader("Analysis Results")
        for finding in findings:
            with st.expander(f"Anomaly Detected: {finding['metric_name']}", expanded=True):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # Visualizing the severity
                    score = finding['severity_score']
                    st.metric("Severity Score", f"{score}/1.0")
                    
                with col2:
                    st.write(f"**Issue:** {finding['finding_summary']}")
                    st.markdown("### 💡 Recommended Action")
                    # Ensure your prompt in TrafficAgent encourages a 'Recommendation' section
                    st.success(finding.get('recommendation', "Contact the supply chain team immediately."))
    
    def close(self):
        self.db.close()