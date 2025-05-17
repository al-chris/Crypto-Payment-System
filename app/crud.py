# app/crud.py

import uuid
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Wallet, Transaction, Log, ForwardingTransaction
from typing import Optional, List
from datetime import datetime, timezone

# --- User CRUD ---

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    results = await session.execute(statement)
    return results.scalars().first()

async def create_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# --- Wallet CRUD ---

async def get_wallet_by_address(session: AsyncSession, address: str) -> Optional[Wallet]:
    statement = select(Wallet).where(Wallet.address == address)
    results = await session.execute(statement)
    return results.scalars().first()

async def get_wallets_by_user(session: AsyncSession, user_id: uuid.UUID) -> List[Wallet]:
    statement = select(Wallet).where(Wallet.user_id == user_id)
    results = await session.execute(statement)
    return list(results.scalars().all())

async def create_wallet(session: AsyncSession, wallet: Wallet) -> Wallet:
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet

# --- Transaction CRUD ---

async def create_transaction(session: AsyncSession, transaction: Transaction) -> Transaction:
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction

async def get_transaction_by_hash(session: AsyncSession, tx_hash: str) -> Optional[Transaction]:
    statement = select(Transaction).where(Transaction.transaction_hash == tx_hash)
    results = await session.execute(statement)
    return results.scalars().first()

async def get_pending_transactions(session: AsyncSession) -> List[Transaction]:
    statement = select(Transaction).where(Transaction.status == "pending")
    results = await session.execute(statement)
    return list(results.scalars().all())

async def update_transaction_status(session: AsyncSession, transaction: Transaction, status: str, confirmations: int):
    transaction.status = status
    transaction.confirmations = confirmations
    transaction.updated_at = datetime.now(timezone.utc)
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction

# --- Log CRUD ---

async def create_log(session: AsyncSession, log: Log) -> Log:
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log

# --- ForwardingTransaction CRUD ---

async def create_forwarding_transaction(session: AsyncSession, ft: ForwardingTransaction) -> ForwardingTransaction:
    session.add(ft)
    await session.commit()
    await session.refresh(ft)
    return ft

async def get_forwarding_transaction_by_hash(session: AsyncSession, tx_hash: str) -> Optional[ForwardingTransaction]:
    statement = select(ForwardingTransaction).where(ForwardingTransaction.tx_hash == tx_hash)
    results = await session.execute(statement)
    return results.scalars().first()

async def get_pending_forwarding_transactions(session: AsyncSession) -> List[ForwardingTransaction]:
    statement = select(ForwardingTransaction).where(ForwardingTransaction.status == "pending")
    results = await session.execute(statement)
    return list(results.scalars().all())

async def update_forwarding_transaction_status(session: AsyncSession, ft: ForwardingTransaction, status: str):
    ft.status = status
    ft.updated_at = datetime.now(timezone.utc)
    session.add(ft)
    await session.commit()
    await session.refresh(ft)
    return ft