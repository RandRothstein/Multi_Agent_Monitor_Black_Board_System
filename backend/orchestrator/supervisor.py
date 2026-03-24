from config.db import SessionLocal
from sqlalchemy import text
from orchestrator.helper import parse_sku_from_ai, run_cases
from model.evidince_model import ChatState
from langchain_google_genai import ChatGoogleGenerativeAI
import os

sessions = {}
class SupervisorAgent:

    def __init__(self):
        self.db = SessionLocal()

        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0,
        )

    def analyze(self, user_query: str,session_id: str):
        try:
            state = self.db.query(ChatState).filter_by(session_id=session_id).first()
            if not state:
                state = ChatState(session_id=session_id, history=[], findings=None)
                self.db.add(state)
            # 2. SKU Management
            sku = state.current_sku

            if not sku:
                # Use a more forceful "System" style prompt
                sku_prompt = (
                    "Task: Extract the SKU ID from the user query.\n"
                    f"User Query: {user_query}\n"
                    "Constraint: Return ONLY the raw SKU ID (e.g., SKU-101). "
                    "Do NOT include code, quotes, or explanations. If no SKU exists, return 'None'."
                )
                res = self.model.invoke(sku_prompt)
                # Strip any whitespace or backticks the model might add
                sku = res.content.strip().replace('`', '')

                if sku and sku.lower() != "none":
                    state.current_sku = sku
                    state.findings = None

            if not sku:
                return {"summary": "Please provide a SKU ID to begin the analysis."}

            # Step 2: Fetch cases
            if state.findings is None:
                print(f"--- Running Agents for {sku} ---")
                query = text("SELECT sku_id, anomaly_type, severity FROM dbo.[case] WHERE sku_id = :sku_id")
                result = self.db.execute(query, {'sku_id': sku})
                cases = result.mappings().fetchall()
            
            # Run the heavy agent logic once
                state.findings = run_cases(self.db, cases) if cases else []
            else:
                print(f"--- Using Cached Findings for {sku} ---")

            # 4. Generate Response using the CACHED findings
            summary_prompt = f"""
            Conversation History: {state.history}
            User Query: {user_query}
            
            Business Findings for {sku}:
            {state.findings}

            Answer the user's query based ONLY on the findings above.
            """
            
            summary = self.model.invoke(summary_prompt)

            # 5. Update History and Commit
            new_history = list(state.history)
            new_history.append({"role": "user", "content": user_query})
            new_history.append({"role": "assistant", "content": summary.content})
            state.history = new_history
            
            self.db.commit()
            return {"summary": summary.content}

        finally:
            self.db.close()