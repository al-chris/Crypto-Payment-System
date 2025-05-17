# app/database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_async_engine(DATABASE_URL, echo=True)



async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
