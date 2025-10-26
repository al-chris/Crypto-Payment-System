# tests/conftest.py

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import SQLModel
from app.database import get_session
from app.main import app
from httpx import AsyncClient, ASGITransport
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_crypto_payment.db")

# Set test environment variables
os.environ.setdefault("MNEMONIC", "test test test test test test test test test test test junk")
os.environ.setdefault("FERNET_KEY", "test_fernet_key_12345678901234567890123456789012")
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency override."""
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user_data() -> Dict[str, str]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }

@pytest.fixture
async def test_transaction_data() -> Dict[str, Any]:
    """Sample transaction data for testing."""
    return {
        "transaction_hash": "0x123456789abcdef",
        "currency": "ETH",
        "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "amount": 1.5
    }