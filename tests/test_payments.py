# tests/test_payments.py

import os
from typing import Dict, Any, List
from httpx import AsyncClient
from unittest.mock import patch

# Mock mnemonic for testing
TEST_MNEMONIC = "test test test test test test test test test test test junk"

class TestPaymentInitiate:
    async def test_initiate_payment_success(self, client: AsyncClient, test_user_data: dict[str, str]) -> None:
        """Test successful payment initiation (wallet creation)."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]

        # Set authorization header
        headers = {"Authorization": f"Bearer {token}"}

        with patch.dict(os.environ, {"MNEMONIC": TEST_MNEMONIC}):
            response = await client.post("/payments/initiate", json={"currency": "ETH"}, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "address" in data
        assert "currency" in data
        assert data["currency"] == "ETH"
        assert "created_at" in data

    async def test_initiate_payment_unauthorized(self, client: AsyncClient) -> None:
        """Test payment initiation without authentication fails."""
        response = await client.post("/payments/initiate", json={"currency": "ETH"})

        assert response.status_code == 401

class TestPaymentSubmit:
    async def test_submit_transaction_success(self, client: AsyncClient, test_user_data: Dict[str, str], test_transaction_data: Dict[str, Any]) -> None:
        """Test successful transaction submission."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a wallet first
        with patch.dict(os.environ, {"MNEMONIC": TEST_MNEMONIC}):
            wallet_response = await client.post("/payments/initiate", json={"currency": "ETH"}, headers=headers)
        wallet_data = wallet_response.json()

        # Submit transaction
        transaction_data = test_transaction_data.copy()
        transaction_data["address"] = wallet_data["address"]

        response = await client.post("/payments/submit", json=transaction_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_hash"] == transaction_data["transaction_hash"]
        assert data["currency"] == transaction_data["currency"]
        assert float(data["amount"]) == transaction_data["amount"]
        assert data["status"] == "pending"

    async def test_submit_duplicate_transaction(self, client: AsyncClient, test_user_data: Dict[str, str], test_transaction_data: Dict[str, Any]) -> None:
        """Test submitting duplicate transaction fails."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a wallet first
        with patch.dict(os.environ, {"MNEMONIC": TEST_MNEMONIC}):
            wallet_response = await client.post("/payments/initiate", json={"currency": "ETH"}, headers=headers)
        wallet_data = wallet_response.json()

        # Submit transaction first time
        transaction_data = test_transaction_data.copy()
        transaction_data["address"] = wallet_data["address"]

        await client.post("/payments/submit", json=transaction_data, headers=headers)

        # Try to submit same transaction again
        response = await client.post("/payments/submit", json=transaction_data, headers=headers)

        assert response.status_code == 400
        assert "Transaction already submitted" in response.json()["detail"]

    async def test_submit_transaction_wrong_wallet(self, client: AsyncClient, test_user_data: Dict[str, str], test_transaction_data: Dict[str, Any]) -> None:
        """Test submitting transaction with wallet that doesn't belong to user fails."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to submit transaction with a random address
        transaction_data = test_transaction_data.copy()
        transaction_data["address"] = "0x1234567890123456789012345678901234567890"  # Random address

        response = await client.post("/payments/submit", json=transaction_data, headers=headers)

        assert response.status_code == 404
        assert "Wallet not found" in response.json()["detail"]

class TestGetTransaction:
    async def test_get_transaction_success(self, client: AsyncClient, test_user_data: Dict[str, str], test_transaction_data: Dict[str, Any]) -> None:
        """Test getting transaction status successfully."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create wallet and submit transaction
        with patch.dict(os.environ, {"MNEMONIC": TEST_MNEMONIC}):
            wallet_response = await client.post("/payments/initiate", json={"currency": "ETH"}, headers=headers)
        wallet_data = wallet_response.json()

        transaction_data = test_transaction_data.copy()
        transaction_data["address"] = wallet_data["address"]
        transaction_data["transaction_hash"] = "0x987654321fedcba"  # Different hash

        submit_response = await client.post("/payments/submit", json=transaction_data, headers=headers)
        transaction = submit_response.json()

        # Get transaction status
        response = await client.get(f"/payments/transactions/{transaction['id']}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction["id"]
        assert data["status"] == "pending"

    async def test_get_transaction_not_found(self, client: AsyncClient, test_user_data: Dict[str, str]) -> None:
        """Test getting non-existent transaction fails."""
        # Register and login user
        await client.post("/register", json=test_user_data)

        login_response = await client.post("/token", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to get non-existent transaction
        response = await client.get("/payments/transactions/12345678-1234-5678-9012-123456789012", headers=headers)

        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]

class TestGetWallets:
    async def test_get_my_wallets_success(self, client: AsyncClient) -> None:
        """Test getting user's wallets successfully."""
        # Register and login user
        wallet_user_data = {
            "email": "wallet@example.com",
            "name": "Wallet User",
            "password": "testpassword123"
        }
        await client.post("/register", json=wallet_user_data)

        login_response = await client.post("/token", data={
            "username": wallet_user_data["email"],
            "password": wallet_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a wallet
        with patch.dict(os.environ, {"MNEMONIC": TEST_MNEMONIC}):
            await client.post("/payments/initiate", json={"currency": "ETH"}, headers=headers)

        # Get wallets
        response = await client.get("/payments/my-wallets", headers=headers)

        assert response.status_code == 200
        data: List[Any] = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["currency"] == "ETH"

    async def test_get_my_wallets_empty(self, client: AsyncClient) -> None:
        """Test getting wallets when user has none."""
        # Register and login user
        empty_user_data = {
            "email": "empty@example.com",
            "name": "Empty User",
            "password": "testpassword123"
        }
        await client.post("/register", json=empty_user_data)

        login_response = await client.post("/token", data={
            "username": empty_user_data["email"],
            "password": empty_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get wallets without creating any
        response = await client.get("/payments/my-wallets", headers=headers)

        assert response.status_code == 200
        data: List[Any] = response.json()
        assert isinstance(data, list)
        assert len(data) == 0