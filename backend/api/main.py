from fastapi import FastAPI
from api.routes.analyze import router as analyze_router
from api.routes.action_plan import router as action_router
from model.evidince_model import Base
from config.db import engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Agent System")

origins =[
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(analyze_router)
app.include_router(action_router)