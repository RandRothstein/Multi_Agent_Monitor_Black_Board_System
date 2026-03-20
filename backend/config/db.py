from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = ("mssql+pyodbc://@localhost\SQLEXPRESS/simpli_home_lakehouse"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&trusted_connection=yes"
                "&TrustServerCertificate=yes"
                )

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)

