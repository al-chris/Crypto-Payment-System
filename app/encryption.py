# app/encryption.py

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Load FERNET_KEY from environment
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY not set in environment variables")

cipher_suite = Fernet(FERNET_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts data using Fernet."""
    encrypted = cipher_suite.encrypt(data.encode()).decode()
    return encrypted

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts data using Fernet."""
    decrypted = cipher_suite.decrypt(encrypted_data.encode()).decode()
    return decrypted