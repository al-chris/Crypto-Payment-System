# app/schemas.py

import uuid
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

# --- User Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str  # Plain password for registration

    @field_validator('password')
    @classmethod
    def password_must_be_valid_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must not exceed 72 bytes')
        return v

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Wallet Schemas ---

class WalletCreate(BaseModel):
    currency: str

class WalletRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    address: str
    currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Transaction Schemas ---

class TransactionSubmit(BaseModel):
    transaction_hash: str
    currency: str
    address: str
    amount: float

class TransactionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    wallet_id: uuid.UUID
    transaction_hash: str
    amount: float
    currency: str
    status: str
    confirmations: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Log Schemas ---

class LogRead(BaseModel):
    id: uuid.UUID
    transaction_id: Optional[uuid.UUID]
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Authentication Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Forwarding Transaction Schemas ---

class ForwardingTransactionRead(BaseModel):
    id: uuid.UUID
    user_wallet_id: uuid.UUID
    tx_hash: str
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ForwardingTransactionCreate(BaseModel):
    user_wallet_id: uuid.UUID
    tx_hash: str
    amount: float