# tests/test_wallet_manager.py

import pytest
from app.wallet_manager import WalletManager
from web3 import Web3

class TestWalletManager:
    def test_wallet_manager_initialization(self):
        """Test WalletManager initializes correctly with mnemonic."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet_manager = WalletManager(test_mnemonic)

        assert wallet_manager.mnemonic == test_mnemonic
        assert wallet_manager.current_index == 0

    def test_wallet_manager_initialization_missing_mnemonic(self):
        """Test WalletManager raises error when mnemonic is not provided."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="MNEMONIC not set in environment variables"):
                WalletManager("")

    def test_generate_new_address(self):
        """Test generating a new Ethereum address."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet_manager = WalletManager(test_mnemonic)

        result = wallet_manager.generate_new_address()

        assert "address" in result
        assert "private_key" in result

        # Verify address is valid Ethereum address
        assert Web3.is_address(result["address"])
        assert result["address"].startswith("0x")
        assert len(result["address"]) == 42

        # Verify private key is valid hex
        assert result["private_key"].startswith("0x")
        assert len(result["private_key"]) == 66  # 0x + 64 hex chars

        # Verify index increments
        assert wallet_manager.current_index == 1

    def test_generate_multiple_addresses(self):
        """Test generating multiple unique addresses."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet_manager = WalletManager(test_mnemonic)

        address1 = wallet_manager.generate_new_address()
        address2 = wallet_manager.generate_new_address()
        address3 = wallet_manager.generate_new_address()

        # All addresses should be different
        assert address1["address"] != address2["address"]
        assert address1["address"] != address3["address"]
        assert address2["address"] != address3["address"]

        # All should be valid addresses
        assert Web3.is_address(address1["address"])
        assert Web3.is_address(address2["address"])
        assert Web3.is_address(address3["address"])

        # Index should be incremented correctly
        assert wallet_manager.current_index == 3

    def test_set_current_index(self):
        """Test setting the current index."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        wallet_manager = WalletManager(test_mnemonic)

        wallet_manager.set_current_index(5)
        assert wallet_manager.current_index == 5

        wallet_manager.generate_new_address()
        assert wallet_manager.current_index == 6

    def test_address_derivation_consistency(self):
        """Test that same mnemonic and index produces same address."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

        # Create two wallet managers with same mnemonic
        wm1 = WalletManager(test_mnemonic)
        wm2 = WalletManager(test_mnemonic)

        # Set same index
        wm1.set_current_index(0)
        wm2.set_current_index(0)

        # Generate addresses
        addr1 = wm1.generate_new_address()
        addr2 = wm2.generate_new_address()

        # Should be identical
        assert addr1["address"] == addr2["address"]
        assert addr1["private_key"] == addr2["private_key"]

    def test_different_mnemonics_produce_different_addresses(self):
        """Test that different mnemonics produce different addresses."""
        mnemonic1 = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        mnemonic2 = "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong"

        wm1 = WalletManager(mnemonic1)
        wm2 = WalletManager(mnemonic2)

        addr1 = wm1.generate_new_address()
        addr2 = wm2.generate_new_address()

        # Should be different
        assert addr1["address"] != addr2["address"]
        assert addr1["private_key"] != addr2["private_key"]