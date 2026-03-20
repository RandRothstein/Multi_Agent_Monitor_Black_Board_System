from fastapi import FastAPI
from api.routes.analyze import router as analyze_router
from api.routes.action_plan import router as action_router
from model.evidince_model import Base
from config.db import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent System")
app.include_router(analyze_router)
app.include_router(action_router)