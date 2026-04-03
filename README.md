🚀 Project Overview
This application uses a React frontend to interact with a FastAPI backend. The core logic is powered by LangGraph, which orchestrates multiple specialized "Worker Agents" (Traffic, Price, Market) overseen by a "Supervisor" LLM (Gemini) that decides the best path of analysis based on both database anomalies and user intent.

🏗 Architecture
The system follows a cyclic graph pattern where a Supervisor acts as a central hub.

Frontend: React, Axios (State management and API communication)

Backend: FastAPI (Asynchronous routing and DB session management)

Orchestration: LangGraph (Stateful, multi-agent workflows)

LLM: Gemini 2.0 Flash (Reasoning, extraction, and summarization)

Database: SQLAlchemy / SQL Server (Storing SKU history and anomaly cases)

🛠 Tech Stack
Frontend
React: Functional components with Hooks for session tracking.

Axios: Configured with base URLs and interceptors for seamless API calls.

Backend
FastAPI: High-performance framework handling the Graph execution.

LangGraph: Manages the GraphState, ensuring findings from one agent are passed to the next.

Pydantic: Strict data validation for LLM structured outputs (Routing decisions).
