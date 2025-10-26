# tests/test_encryption.py

import pytest
import os
from unittest.mock import patch

class TestEncryption:
    def test_encrypt_data(self):
        """Test encrypting data."""
        test_key = "test_fernet_key_12345678901234567890123456789012"  # 32 bytes for Fernet

        with patch.dict(os.environ, {"FERNET_KEY": test_key}):
            # Need to reload the module to pick up the new key
            import importlib
            import app.encryption
            importlib.reload(app.encryption)

            data = "test_private_key_123"
            encrypted = app.encryption.encrypt_data(data)

            assert encrypted != data
            assert isinstance(encrypted, str)
            assert len(encrypted) > 0

    def test_decrypt_data(self):
        """Test decrypting data."""
        test_key = "test_fernet_key_12345678901234567890123456789012"

        with patch.dict(os.environ, {"FERNET_KEY": test_key}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)

            original_data = "test_private_key_123"
            encrypted = app.encryption.encrypt_data(original_data)
            decrypted = app.encryption.decrypt_data(encrypted)

            assert decrypted == original_data

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt is reversible."""
        test_key = "another_test_key_123456789012345678901234567890"

        with patch.dict(os.environ, {"FERNET_KEY": test_key}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)

            test_cases = [
                "simple_string",
                "private_key_0x123456789abcdef",
                "a_very_long_private_key_that_should_still_work_properly_with_fernet_encryption",
                "special_chars_!@#$%^&*()",
                "unicode_测试数据"
            ]

            for original in test_cases:
                encrypted = app.encryption.encrypt_data(original)
                decrypted = app.encryption.decrypt_data(encrypted)
                assert decrypted == original

    def test_different_keys_produce_different_results(self):
        """Test that different keys produce different encrypted results."""
        key1 = "key_one_1234567890123456789012345678901234567890"
        key2 = "key_two_1234567890123456789012345678901234567890"

        data = "test_data"

        with patch.dict(os.environ, {"FERNET_KEY": key1}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)
            encrypted1 = app.encryption.encrypt_data(data)

        with patch.dict(os.environ, {"FERNET_KEY": key2}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)
            encrypted2 = app.encryption.encrypt_data(data)

        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decrypting with wrong key fails."""
        key1 = "key_one_1234567890123456789012345678901234567890"
        key2 = "key_two_1234567890123456789012345678901234567890"

        data = "test_data"

        with patch.dict(os.environ, {"FERNET_KEY": key1}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)
            encrypted = app.encryption.encrypt_data(data)

        with patch.dict(os.environ, {"FERNET_KEY": key2}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)

            with pytest.raises(Exception):  # Fernet will raise an exception for wrong key
                app.encryption.decrypt_data(encrypted)

    def test_encryption_missing_key(self):
        """Test that encryption fails when FERNET_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="FERNET_KEY not set in environment variables"):
                import importlib
                import app.encryption
                importlib.reload(app.encryption)

    def test_empty_string_encryption(self):
        """Test encrypting empty string."""
        test_key = "test_key_empty_12345678901234567890123456789012"

        with patch.dict(os.environ, {"FERNET_KEY": test_key}):
            import importlib
            import app.encryption
            importlib.reload(app.encryption)

            encrypted = app.encryption.encrypt_data("")
            decrypted = app.encryption.decrypt_data(encrypted)

            assert decrypted == ""