import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
load_dotenv()
# MUST use the async variant of the driver (aioodbc)
# Format: mssql+aioodbc://<user>:<pass>@<host>/<db>?driver=ODBC+Driver+18...
DATABASE_URL = os.getenv("DATABASE_URL")

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

