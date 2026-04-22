import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# MUST use the async variant of the driver (aioodbc)
# Format: mssql+aioodbc://<user>:<pass>@<host>/<db>?driver=ODBC+Driver+18...
DATABASE_URL = (
    "mssql+aioodbc://rrothstein:Wednesday_2026@142.202.170.44/simpli_home_lakehouse"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
    "&Encrypt=yes"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)

# Use AsyncSessionLocal throughout the app
AsyncSessionLocal = async_sessionmaker(
    bind=engine
)

