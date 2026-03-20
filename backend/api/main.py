from fastapi import FastAPI
from api.routes.analyze import router as analyze_router
from api.routes.action_plan import router as action_router

app = FastAPI(title="Multi-Agent System")

app.include_router(analyze_router)
app.include_router(action_router)