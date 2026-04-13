from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = ("mssql+pyodbc://rrothstein:Wednesday_2026@142.202.170.44/simpli_home_lakehouse"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&TrustServerCertificate=yes"
                "&Encrypt=yes"  
                )

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(bind=engine)

