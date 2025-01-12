# app/models.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str  # Store hashed passwords
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    address: str = Field(index=True, unique=True)
    currency: str
    private_key: str  # Encrypted
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    wallet_id: int = Field(foreign_key="wallet.id")
    transaction_hash: str = Field(index=True, unique=True)
    currency: str
    status: str = Field(default="pending")  # pending, confirmed, failed
    confirmations: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)