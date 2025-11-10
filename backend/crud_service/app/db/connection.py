import os
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from config import settings

DATABASE_URL = settings.CRUD_DATABASE_URL
if DATABASE_URL is None:
    raise ValueError("Database URL is not configured. Check your environment variables.")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Asynchronous session context manager for interacting with the database."""
    async with async_session() as session:
        yield session

async def test_connection():
    """Test the database connection."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        raise
