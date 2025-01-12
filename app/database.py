# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)

# Use AsyncSession here, not SQLModel
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,     # <-- This is crucial
    expire_on_commit=False,
    autoflush=False
)

async def get_session():
    async with async_session() as session:
        yield session
