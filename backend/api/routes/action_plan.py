from fastapi import APIRouter
from sqlalchemy import text
from config.db import SessionLocal

router = APIRouter()

@router.post("/action-plan")
def save_action(sku: str, action: str):
    db = SessionLocal()

    try:
        query = text("""
            INSERT INTO dbo.action_plans
            (sku_id, action_note, status, created_at)
            VALUES (:s, :a, 'Monitoring', GETDATE())
        """)

        db.execute(query, {'s': sku, 'a': action})
        db.commit()

        return {"status": "saved"}

    finally:
        db.close()