from config.db import SessionLocal
from sqlalchemy import text
from orchestrator.helper import parse_sku_from_ai,run_cases
from langchain.agents import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
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

        self.model = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            google_api_key = os.getenv('GOOGLE_API_KEY'),
            temperature = 0,
        )
    
    def user_interface(self):
            # 1. Initialize variables to avoid NameErrors
            if "current_sku" not in st.session_state:
                st.session_state.current_sku = None
            if "show_action_plan" not in st.session_state:
                st.session_state.show_action_plan = False

            if not st.session_state.show_action_plan:
                user_query = st.text_area("Ask your question about any product (e.g., 'Check status for SKU_123')", height=100)
                
                if st.button('Analyze') and user_query:
                    messages = [
                        {"role": "user", "content": f"Extract the SKU ID from this query: {user_query}. Return ONLY the ID (e.g. SKU-002). If no ID is found, return 'None'."}
                    ]
                    response = self.model.invoke(messages)
                    # Ensure this helper handles string "None" vs NoneType
                    extracted_sku = parse_sku_from_ai(response.content) 
                    
                    if extracted_sku and str(extracted_sku).lower() != "none":
                        # Use a context manager or ensure the session is handled
                        st.session_state.current_sku = extracted_sku
                        query = text("""
                            SELECT sku_id, anomaly_type, severity
                            FROM dbo.[case] 
                            WHERE sku_id = :sku_id
                        """)
                        result = self.db.execute(query, {'sku_id': extracted_sku})
                        cases = result.mappings().fetchall()
                        
                        if cases:
                            findings = run_cases(self.db, cases)   
                            self.display_results(findings)
                        else:
                            st.warning(f"No anomalies found in the database for SKU: {extracted_sku}")
                    else:
                        st.error("Please provide a valid SKU ID in your query.")

            # 2. Guard the Action Plan section
            if st.session_state.current_sku:
                extracted_sku = st.session_state.current_sku
                st.divider()
                st.subheader("📝 Meeting Action Plan")

                # Fetch previous notes
                prev_notes = self.db.execute(
                    text("SELECT action_note FROM action_plans WHERE sku_id = :s ORDER BY created_at DESC"), 
                    {'s': extracted_sku}
                ).fetchone()

                if prev_notes:
                    st.warning(f"**Last Meeting Note:** {prev_notes[0]}")
                
                action = st.text_area(f"What action are we taking for {extracted_sku}?")    
                
                col1,col2 = st.columns(2)

                with col1:
                    if st.button("Save Action & Monitor"):
                        if action:
                            try:
                                insert_query = text("""
                                    INSERT INTO dbo.action_plans (sku_id, action_note, status, created_at) 
                                    VALUES (:s, :a, 'Monitoring', GETDATE())
                                """)
                                self.db.execute(insert_query, {'s': extracted_sku, 'a': action})
                                self.db.commit()

                                st.session_state.current_sku = None
                                st.session_state.show_action_plan = False
                                st.success('Action saved and Saul is Monitoring ...')
                                st.rerun()

                            except Exception as e:
                                self.db.rollback()
                                st.error(f"Error: {e}")
                        else:
                            st.error("Please enter a note.")
                with col2:
                    if st.button("Cancel"):
                        st.session_state.show_action_plan = False
                        st.session_state.current_sku = None
                        st.rerun()

                        
                        
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