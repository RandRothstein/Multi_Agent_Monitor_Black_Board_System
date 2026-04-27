from sqlalchemy import Column, Integer, String, Float, DateTime,Text,JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.dialects.mssql import NVARCHAR
# 1. This creates the registry
Base = declarative_base()

# 2. YOU MUST INCLUDE (Base) HERE so SQLAlchemy can see it
class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)

    product_id = Column(String(50), index=True)
    agent_name = Column(String(50))

    anomaly_type = Column(String(50), index=True)
    risk_score = Column(Float)

    # NEW: store full SA-2 structured output
    signals = Column(JSON)

    finding_summary = Column(Text)
    recommendation = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(50), index=True)
    retailer = Column(String(50))
    anomaly_type = Column(String(50))
    severity = Column(Float)
    revenue_impact = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionPlan(Base):
    __tablename__ = "action_plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(50))
    action_note = Column(Text) # e.g., "Fixed Target promo issue"
    status = Column(String(20), default="Monitoring") 
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatState(Base):
    __tablename__ = "chat_state"

    # Indexing is vital for scaling. A session_id lookup must be O(1).
    session_id = Column(String(100), primary_key=True, index=True)
    current_sku = Column(String(50), nullable=True, index=True)

    # Use Text(None) or NVARCHAR(MAX) for JSON in SQL Server to avoid truncation
    findings = Column(JSON, nullable=True)
    history = Column(JSON, default=[])