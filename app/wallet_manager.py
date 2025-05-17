# app/wallet_manager.py

from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes # type: ignore
from web3 import Web3
import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()

# Load your mnemonic (seed phrase) from environment variables
MNEMONIC = os.getenv("MNEMONIC")  # e.g., "abandon abandon ..."

if not MNEMONIC:
    raise ValueError("MNEMONIC not set in environment variables")

class WalletManager:
    def __init__(self, mnemonic: str):
        self.mnemonic = mnemonic
        # Generate seed from mnemonic
        seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()
        # Initialize Bip44 for Ethereum
        self.bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        # Change 0 for external chain
        self.bip44_acc = self.bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
        # Initialize index based on existing wallets
        self.current_index = 0  # This should be set based on existing wallets

    def set_current_index(self, index: int):
        self.current_index = index

    def generate_new_address(self) -> dict[str, Any]:
        """
        Generates a new Ethereum address using Bip44 standard.
        Returns a dictionary with address and private key.
        """
        # Derive the path m/44'/60'/0'/0/index
        bip44_addr = self.bip44_acc.AddressIndex(self.current_index)
        address: str = bip44_addr.PublicKey().ToAddress()
        private_key: str = bip44_addr.PrivateKey().Raw().ToHex()
        
        # Increment index for next address
        self.current_index += 1

        return {
            "address": Web3.to_checksum_address(address),
            "private_key": private_key
        }