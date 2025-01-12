# app/tasks/transaction_monitor.py

import os
import asyncio
import nest_asyncio
from celery import Celery
from sqlalchemy.orm import Session
from sqlmodel import select
import httpx

from ..database import engine, async_session  # Use async_session
from ..models import Transaction, Wallet, Log
from ..crud import update_transaction_status, create_log

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

celery = Celery("tasks")

@celery.task
def monitor_transactions():
    nest_asyncio.apply()
    asyncio.run(_monitor_transactions_async())

async def _monitor_transactions_async():
    async with async_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.status == "pending"))
        pending_transactions = result.scalars().all()
        if not pending_transactions:
            return

        address_to_txs = {}
        for tx in pending_transactions:
            wallet = await session.get(Wallet, tx.wallet_id)
            if wallet:
                address_to_txs.setdefault(wallet.address, []).append(tx)

        async with httpx.AsyncClient() as client:
            for address, txs in address_to_txs.items():
                url = (
                    "https://api.etherscan.io/api"
                    f"?module=account&action=txlist&address={address}"
                    f"&startblock=0&endblock=99999999&sort=asc"
                    f"&apikey={ETHERSCAN_API_KEY}"
                )
                try:
                    response = await client.get(url)
                    data = response.json()
                    if data.get("status") != "1":
                        continue

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
                                        message=(
                                            f"Transaction {tx_hash} set to {status} "
                                            f"with {confirmations} confirmations."
                                        )
                                    )
                                    await create_log(session, log)
                except Exception as e:
                    log = Log(
                        transaction_id=None,
                        message=f"Error fetching transactions for {address}: {str(e)}"
                    )
                    await create_log(session, log)

async def _get_latest_block(client: httpx.AsyncClient) -> int:
    url = (
        "https://api.etherscan.io/api"
        f"?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
    )
    response = await client.get(url)
    data = response.json()
    return int(data["result"], 16) if data.get("result") else 0
