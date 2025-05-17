# app/routers/payments.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from typing import List
from ..schemas import TransactionSubmit, TransactionRead, WalletRead
from ..crud import (
    create_wallet,
    get_wallet_by_address,
    get_wallets_by_user,
    create_transaction,
    get_transaction_by_hash
)
from ..models import User, Wallet, Transaction
from ..dependencies import get_session, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from ..wallet_manager import WalletManager
from ..encryption import encrypt_data
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize WalletManager
# from ..encryption import decrypt_data

# For simplicity, initialize WalletManager here. In production, consider dependency injection.
from ..wallet_manager import WalletManager

MNEMONIC = os.getenv("MNEMONIC")

if not MNEMONIC:
    raise ValueError("MNEMONIC not set in environment variables")

wallet_manager = WalletManager(MNEMONIC)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)

@router.post("/initiate", response_model=WalletRead)
async def initiate_payment(
    wallet_create: dict[str, str] = {"currency": "ETH"},  # Default to ETH; adjust as needed
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    currency = wallet_create.get("currency", "ETH")
    
    # Generate a new unique wallet address
    new_wallet_data = wallet_manager.generate_new_address()
    address = new_wallet_data["address"]
    private_key = new_wallet_data["private_key"]

    # Encrypt the private key before storing
    encrypted_private_key = encrypt_data(private_key)

    # Create Wallet entry
    wallet = Wallet(
        user_id=current_user.id,
        address=address,
        currency=currency,
        private_key=encrypted_private_key
    )

    try:
        wallet = await create_wallet(session, wallet)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Wallet creation failed")

    return wallet

@router.post("/submit", response_model=TransactionRead)
async def submit_transaction(
    transaction: TransactionSubmit,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Retrieve all wallets for the user
    wallets = await get_wallets_by_user(session, current_user.id)
    if not wallets:
        raise HTTPException(status_code=400, detail="No wallets found for the user. Initiate a wallet first.")

    # For simplicity, assume the user uses any of their wallets to send the transaction
    # You can modify this to specify which wallet/address was used
    # Here, we require the user to specify which wallet address was used for the transaction

    # To implement this, ensure that the user provides the address used
    # Update the TransactionSubmit schema to include the address used
    # Let's adjust the TransactionSubmit schema accordingly

    # Assuming transaction has an 'address' field specifying which wallet was used
    address = transaction.address
    wallet = await get_wallet_by_address(session, address=address)
    if not wallet or wallet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Wallet not found for the user")

    # Check if the transaction already exists
    existing_tx = await get_transaction_by_hash(session, transaction.transaction_hash)
    if existing_tx:
        raise HTTPException(status_code=400, detail="Transaction already submitted")

    # Create a new transaction record
    new_transaction = Transaction(
        user_id=current_user.id,
        wallet_id=wallet.id,
        transaction_hash=transaction.transaction_hash,
        currency=transaction.currency,
        status="pending",
        amount=transaction.amount
    )
    try:
        new_transaction = await create_transaction(session, new_transaction)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Transaction already exists")

    return new_transaction

@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
async def get_transaction_status(
    transaction_id: int, 
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    transaction = await session.get(Transaction, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.get("/my-wallets", response_model=List[WalletRead])
async def get_my_wallets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    wallets = await get_wallets_by_user(session, current_user.id)
    return wallets