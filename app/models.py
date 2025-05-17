# app/models.py
import uuid
from sqlmodel import SQLModel, Field, Column, DateTime
from datetime import datetime, timezone
from typing import Optional

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, unique=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str  # Store hashed passwords
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column=Column(DateTime(timezone=True))
    )

class Wallet(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, unique=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    address: str = Field(index=True, unique=True)
    currency: str
    private_key: str  # Encrypted
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column=Column(DateTime(timezone=True))
    )

class Transaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, unique=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    wallet_id: uuid.UUID = Field(foreign_key="wallet.id")
    transaction_hash: str = Field(index=True, unique=True)
    amount: float
    currency: str
    status: str = Field(default="pending")  # pending, confirmed, failed
    confirmations: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), 
            onupdate=datetime.now(timezone.utc)
        )
    )

class Log(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, unique=True)
    transaction_id: Optional[uuid.UUID] = Field(default=None, foreign_key="transaction.id")
    message: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column=Column(DateTime(timezone=True))
    )

# Forwarding Transaction Model
class ForwardingTransaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, unique=True)
    user_wallet_id: uuid.UUID = Field(foreign_key="wallet.id")
    tx_hash: str = Field(index=True, unique=True)
    amount: float  # Amount in ETH or relevant currency
    status: str = Field(default="pending")  # pending, sent, failed
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), 
            onupdate=datetime.now(timezone.utc)
        )
    )