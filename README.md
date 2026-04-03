# 🔍 Evidence AI Analysis Engine

A sophisticated multi-agent orchestration system designed to investigate SKU performance anomalies using a **Supervisor-Worker** pattern.

---

## 🏗️ Architecture Overview

The system follows a cyclic graph pattern where a central **Supervisor** (Gemini) evaluates the state and delegates tasks to specialized analysis nodes.

* **Frontend:** React (UI) + Axios (API Communication)
* **Backend:** FastAPI (Async Web Framework)
* **Orchestration:** LangGraph (Stateful Multi-Agent Workflows)
* **LLM:** Gemini 2.0 Flash (Reasoning & Extraction)
* **Database:** SQL Server / SQLAlchemy (Persistence & Case Management)

---

## 🚀 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React, Axios, Tailwind CSS |
| **Backend** | FastAPI, Uvicorn |
| **AI Framework** | LangGraph, LangChain |
| **LLM** | Google Gemini 2.0 Flash |
| **Database** | SQLAlchemy (ORM), SQL Server |
| **Validation** | Pydantic v2 |

---

## 📂 Project Structure

<img width="372" height="867" alt="image" src="https://github.com/user-attachments/assets/d7856584-a83d-4845-acd2-8eebbbb1a0b1" />
