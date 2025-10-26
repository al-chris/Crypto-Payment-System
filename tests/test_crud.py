# tests/test_crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    get_user_by_email, create_user,
    get_wallet_by_address, get_wallets_by_user, create_wallet,
    create_transaction, get_transaction_by_hash,
    get_pending_transactions, update_transaction_status
)
from app.models import User, Wallet, Transaction
from decimal import Decimal
from app.auth import hash_password

class TestUserCRUD:
    async def test_create_user(self, test_session: AsyncSession) -> None:
        """Test creating a user."""
        user = User(
            email="crud_test@example.com",
            name="CRUD Test User",
            hashed_password=hash_password("testpassword")
        )

        created_user = await create_user(test_session, user)

        assert created_user.id is not None
        assert created_user.email == "crud_test@example.com"
        assert created_user.name == "CRUD Test User"
        assert created_user.hashed_password == hash_password("testpassword")

    async def test_get_user_by_email(self, test_session: AsyncSession) -> None:
        """Test getting user by email."""
        user = User(
            email="get_test@example.com",
            name="Get Test User",
            hashed_password=hash_password("testpassword")
        )
        await create_user(test_session, user)

        retrieved_user = await get_user_by_email(test_session, "get_test@example.com")

        assert retrieved_user is not None
        assert retrieved_user.email == "get_test@example.com"
        assert retrieved_user.name == "Get Test User"

    async def test_get_user_by_email_not_found(self, test_session: AsyncSession) -> None:
        """Test getting non-existent user returns None."""
        retrieved_user = await get_user_by_email(test_session, "nonexistent@example.com")

        assert retrieved_user is None

class TestWalletCRUD:
    async def test_create_wallet(self, test_session: AsyncSession) -> None:
        """Test creating a wallet."""
        # First create a user
        user = User(
            email="wallet_test@example.com",
            name="Wallet Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0x1234567890123456789012345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        created_wallet = await create_wallet(test_session, wallet)

        assert created_wallet.id is not None
        assert created_wallet.user_id == user.id
        assert created_wallet.address == "0x1234567890123456789012345678901234567890"
        assert created_wallet.currency == "ETH"

    async def test_get_wallet_by_address(self, test_session: AsyncSession) -> None:
        """Test getting wallet by address."""
        # Create user and wallet
        user = User(
            email="wallet_get_test@example.com",
            name="Wallet Get Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0xabcdef123456789012345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        await create_wallet(test_session, wallet)

        retrieved_wallet = await get_wallet_by_address(test_session, "0xabcdef123456789012345678901234567890")

        assert retrieved_wallet is not None
        assert retrieved_wallet.address == wallet.address
        assert retrieved_wallet.user_id == user.id

    async def test_get_wallets_by_user(self, test_session: AsyncSession) -> None:
        """Test getting all wallets for a user."""
        # Create user
        user = User(
            email="multi_wallet_test@example.com",
            name="Multi Wallet Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        # Create multiple wallets
        wallet1 = Wallet(
            user_id=user.id,
            address="0x1111111111111111111111111111111111111111",
            currency="ETH",
            private_key="encrypted_key_1"
        )
        wallet2 = Wallet(
            user_id=user.id,
            address="0x2222222222222222222222222222222222222222",
            currency="BTC",
            private_key="encrypted_key_2"
        )

        await create_wallet(test_session, wallet1)
        await create_wallet(test_session, wallet2)

        wallets = await get_wallets_by_user(test_session, user.id)

        assert len(wallets) == 2
        addresses = [w.address for w in wallets]
        assert "0x1111111111111111111111111111111111111111" in addresses
        assert "0x2222222222222222222222222222222222222222" in addresses

class TestTransactionCRUD:
    async def test_create_transaction(self, test_session: AsyncSession) -> None:
        """Test creating a transaction."""
        # Create user and wallet first
        user = User(
            email="transaction_test@example.com",
            name="Transaction Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0xtransactiontest12345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        wallet = await create_wallet(test_session, wallet)

        transaction = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            transaction_hash="0xabcdef1234567890abcdef1234567890abcdef",
            amount=Decimal("2.5"),
            currency="ETH",
            status="pending"
        )
        created_transaction = await create_transaction(test_session, transaction)

        assert created_transaction.id is not None
        assert created_transaction.transaction_hash == "0xabcdef1234567890abcdef1234567890abcdef"
        assert created_transaction.amount == Decimal("2.5")
        assert created_transaction.status == "pending"

    async def test_get_transaction_by_hash(self, test_session: AsyncSession) -> None:
        """Test getting transaction by hash."""
        # Create user, wallet, and transaction
        user = User(
            email="get_transaction_test@example.com",
            name="Get Transaction Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0xgettransactiontest12345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        wallet = await create_wallet(test_session, wallet)

        transaction = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            transaction_hash="0xgettest1234567890abcdef1234567890abcdef",
            amount=Decimal("1.0"),
            currency="ETH",
            status="pending"
        )
        await create_transaction(test_session, transaction)

        retrieved_transaction = await get_transaction_by_hash(test_session, "0xgettest1234567890abcdef1234567890abcdef")

        assert retrieved_transaction is not None
        assert retrieved_transaction.transaction_hash == transaction.transaction_hash
        assert retrieved_transaction.amount == Decimal("1.0")

    async def test_get_pending_transactions(self, test_session: AsyncSession) -> None:
        """Test getting all pending transactions."""
        # Create user and wallet
        user = User(
            email="pending_test@example.com",
            name="Pending Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0xpendingtest123456789012345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        wallet = await create_wallet(test_session, wallet)

        # Create multiple transactions with different statuses
        pending_tx = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            transaction_hash="0xpending1234567890abcdef1234567890abcdef",
            amount=Decimal("1.0"),
            currency="ETH",
            status="pending"
        )
        confirmed_tx = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            transaction_hash="0xconfirmed1234567890abcdef1234567890abcdef",
            amount=Decimal("2.0"),
            currency="ETH",
            status="confirmed"
        )

        await create_transaction(test_session, pending_tx)
        await create_transaction(test_session, confirmed_tx)

        pending_transactions = await get_pending_transactions(test_session)

        assert len(pending_transactions) >= 1  # At least our pending transaction
        pending_hashes = [tx.transaction_hash for tx in pending_transactions]
        assert "0xpending1234567890abcdef1234567890abcdef" in pending_hashes
        assert "0xconfirmed1234567890abcdef1234567890abcdef" not in pending_hashes

    async def test_update_transaction_status(self, test_session: AsyncSession) -> None:
        """Test updating transaction status."""
        # Create user, wallet, and transaction
        user = User(
            email="update_test@example.com",
            name="Update Test User",
            hashed_password=hash_password("testpassword")
        )
        user = await create_user(test_session, user)

        wallet = Wallet(
            user_id=user.id,
            address="0xupdatetest123456789012345678901234567890",
            currency="ETH",
            private_key="encrypted_private_key"
        )
        wallet = await create_wallet(test_session, wallet)

        transaction = Transaction(
            user_id=user.id,
            wallet_id=wallet.id,
            transaction_hash="0xupdatetest1234567890abcdef1234567890abcdef",
            amount=Decimal("1.5"),
            currency="ETH",
            status="pending"
        )
        transaction = await create_transaction(test_session, transaction)

        # Update status
        updated_transaction = await update_transaction_status(test_session, transaction, "confirmed", 6)

        assert updated_transaction.status == "confirmed"
        assert updated_transaction.confirmations == 6
        assert updated_transaction.updated_at is not None