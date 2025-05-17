# app/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- User Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str  # Plain password for registration

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Wallet Schemas ---

class WalletCreate(BaseModel):
    currency: str

class WalletRead(BaseModel):
    id: int
    user_id: int
    address: str
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Transaction Schemas ---

class TransactionSubmit(BaseModel):
    transaction_hash: str
    currency: str
    address: str
    amount: float

class TransactionRead(BaseModel):
    id: int
    user_id: int
    wallet_id: int
    transaction_hash: str
    currency: str
    status: str
    confirmations: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Log Schemas ---

class LogRead(BaseModel):
    id: int
    transaction_id: Optional[int]
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

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
    id: int
    user_wallet_id: int
    tx_hash: str
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ForwardingTransactionCreate(BaseModel):
    user_wallet_id: int
    tx_hash: str
    amount: float