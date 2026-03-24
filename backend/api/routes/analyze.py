from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.supervisor import SupervisorAgent

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    session_id: str

@router.post("/analyze")
def analyze(request: QueryRequest):
    supervisor = SupervisorAgent()
    return supervisor.analyze(request.query,request.session_id)