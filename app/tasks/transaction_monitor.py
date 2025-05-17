import os
import asyncio
import nest_asyncio # type: ignore
from celery import Celery # type: ignore
from sqlmodel import select
import httpx
from web3 import Web3
from dotenv import load_dotenv
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import engine
from ..models import Transaction, Wallet, Log, ForwardingTransaction
from ..crud import (
    update_transaction_status,
    create_log,
    create_forwarding_transaction,
    update_forwarding_transaction_status,
    get_pending_forwarding_transactions
)
from ..encryption import decrypt_data

load_dotenv()

# Environment variables
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ORG_WALLET_ADDRESS = os.getenv("ORG_WALLET_ADDRESS")
ORG_WALLET_PRIVATE_KEY_ENCRYPTED = os.getenv("ORG_WALLET_PRIVATE_KEY_ENCRYPTED")

# Validation
if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY not set in environment variables")
if not ORG_WALLET_ADDRESS or not ORG_WALLET_PRIVATE_KEY_ENCRYPTED:
    raise ValueError("Organization wallet details are not set in environment variables")

# Web3 setup
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URL")))
ORG_WALLET_PRIVATE_KEY = decrypt_data(ORG_WALLET_PRIVATE_KEY_ENCRYPTED)

celery = Celery(
    "tasks", 
    broker=os.getenv("CELERY_BROKER_URL"), 
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

@celery.task() # type: ignore
def monitor_transactions():
    nest_asyncio.apply() # type: ignore
    asyncio.run(_monitor_transactions_async())

async def _monitor_transactions_async():
    async with AsyncSession(engine) as session:
        # Monitor pending transactions
        result = await session.execute(select(Transaction).where(Transaction.status == "pending"))
        pending_transactions = result.scalars().all()
        if not pending_transactions:
            return

        address_to_txs: dict[str, list[Any]] = {}
        for tx in pending_transactions:
            wallet = await session.get(Wallet, tx.wallet_id)
            if wallet:
                address_to_txs.setdefault(wallet.address, []).append(tx)

        async with httpx.AsyncClient() as client:
            for address, txs in address_to_txs.items():
                try:
                    await process_address_transactions(client, session, address, txs)
                except Exception as e:
                    await create_log(
                        session,
                        Log(
                            transaction_id=None,
                            message=f"Error processing transactions for {address}: {str(e)}"
                        )
                    )

        # Process pending forwarding transactions
        await process_pending_forwarding_transactions(session)

async def process_address_transactions(client: httpx.AsyncClient, session: AsyncSession, address: str, txs: list[Any]):
    url = (
        "https://api.etherscan.io/api"
        f"?module=account&action=txlist&address={address}"
        f"&startblock=0&endblock=99999999&sort=asc"
        f"&apikey={ETHERSCAN_API_KEY}"
    )
    
    response = await client.get(url)
    data = response.json()
    if data.get("status") != "1":
        return

    transactions = data["result"]
    current_block = await _get_latest_block(client)
    
    for eth_tx in transactions:
        tx_hash = eth_tx["hash"]
        tx_status = eth_tx["txreceipt_status"]
        block_number = int(eth_tx["blockNumber"])
        confirmations = current_block - block_number + 1

        for db_tx in txs:
            if db_tx.transaction_hash.lower() == tx_hash.lower():
                if db_tx.status == "pending" and confirmations >= 12:
                    status = "confirmed" if tx_status == "1" else "failed"
                    await update_transaction_status(session, db_tx, status, confirmations)
                    
                    log = Log(
                        transaction_id=db_tx.id,
                        message=f"Transaction {tx_hash} set to {status} with {confirmations} confirmations."
                    )
                    await create_log(session, log)

                    if status == "confirmed":
                        wallet = await session.get(Wallet, db_tx.wallet_id)
                        if not wallet:
                            raise ValueError("Wallet is None")
                        await initiate_forwarding(session, db_tx, wallet)

async def process_pending_forwarding_transactions(session: AsyncSession):
    forwarding_txs = await get_pending_forwarding_transactions(session)
    for ft in forwarding_txs:
        user_wallet = await session.get(Wallet, ft.user_wallet_id)
        if not user_wallet:
            await update_forwarding_transaction_status(session, ft, "failed")
            continue

        try:
            decrypted_private_key = decrypt_data(user_wallet.private_key)
            tx_receipt = await send_forwarding_transaction(decrypted_private_key, ft.amount)
            
            ft.tx_hash = tx_receipt['transactionHash'].hex()
            await update_forwarding_transaction_status(session, ft, "sent")
            
            await create_log(
                session,
                Log(
                    transaction_id=None,
                    message=f"Forwarding transaction {ft.tx_hash} sent to organization wallet."
                )
            )
        except Exception as e:
            await update_forwarding_transaction_status(session, ft, "failed")
            await create_log(
                session,
                Log(
                    transaction_id=None,
                    message=f"Failed to forward transaction: {str(e)}"
                )
            )

async def _get_latest_block(client: httpx.AsyncClient) -> int:
    url = (
        "https://api.etherscan.io/api"
        f"?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
    )
    response = await client.get(url)
    data = response.json()
    return int(data["result"], 16) if data.get("result") else 0

async def initiate_forwarding(session: AsyncSession, transaction: Transaction, wallet: Wallet):
    """Create a ForwardingTransaction entry to be processed."""
    ft = ForwardingTransaction(
        user_wallet_id=wallet.id,
        tx_hash=transaction.transaction_hash,
        amount=transaction.amount
    )
    await create_forwarding_transaction(session, ft)

async def send_forwarding_transaction(private_key: str, amount: float) -> dict[str, Any]:
    """Sends ETH from the user's wallet to the organization's wallet."""
    account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)

    tx: dict[str, Any] = {
        'nonce': nonce,
        'to': ORG_WALLET_ADDRESS,
        'value': w3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,  # Dynamic gas price
        'chainId': 1  # Mainnet
    }

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return {'transactionHash': tx_hash}