from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.supervisor import SupervisorAgent

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/analyze")
def analyze(request: QueryRequest):
    supervisor = SupervisorAgent()
    return supervisor.analyze(request.query)