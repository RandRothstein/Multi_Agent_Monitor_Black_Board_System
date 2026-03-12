from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 1. This creates the registry
Base = declarative_base()

# 2. YOU MUST INCLUDE (Base) HERE so SQLAlchemy can see it
class Evidence(Base):
    __tablename__ = "evidence"

    # 3. Defining the columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), index=True)
    agent_name = Column(String(50))
    metric_name = Column(String(100))
    metric_value = Column(Float)
    severity_score = Column(Float)
    finding_summary = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(50), index=True)
    retailer = Column(String(50))
    anomaly_type = Column(String(50))
    severity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
