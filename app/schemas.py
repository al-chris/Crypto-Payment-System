# app/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
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
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str