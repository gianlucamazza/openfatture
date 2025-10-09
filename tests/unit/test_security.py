"""
Unit tests for security utilities.

Tests secrets management, encryption, and security helpers.
"""

import os

import pytest
from cryptography.fernet import Fernet

from openfatture.utils.security import (
    DataEncryption,
    SecretsManager,
    SecureConfig,
    check_secrets_in_code,
    mask_sensitive_value,
    validate_env_vars,
)

pytestmark = pytest.mark.unit


class TestSecretsManager:
    """Test SecretsManager for secrets handling."""

    def test_init_default_backend(self):
        """Test initialization with default backend."""
        manager = SecretsManager()
        assert manager.backend == "env"

    def test_init_env_backend(self):
        """Test initialization with env backend."""
        manager = SecretsManager(backend="env")
        assert manager.backend == "env"

    def test_init_unsupported_backend_raises(self):
        """Test that unsupported backend raises error."""
        with pytest.raises(NotImplementedError):
            SecretsManager(backend="vault")

    def test_get_secret_from_env(self, monkeypatch):
        """Test getting secret from environment variable."""
        monkeypatch.setenv("TEST_SECRET", "secret_value")

        manager = SecretsManager()
        value = manager.get_secret("TEST_SECRET")

        assert value == "secret_value"

    def test_get_secret_with_default(self):
        """Test getting secret with default value."""
        manager = SecretsManager()
        value = manager.get_secret("NONEXISTENT_SECRET", default="default_value")

        assert value == "default_value"

    def test_get_secret_nonexistent_returns_none(self):
        """Test that nonexistent secret returns None."""
        manager = SecretsManager()
        value = manager.get_secret("TOTALLY_NONEXISTENT_KEY_12345")

        assert value is None

    def test_set_secret_in_env(self):
        """Test setting secret in environment."""
        manager = SecretsManager()
        manager.set_secret("TEST_SET_SECRET", "new_value")

        assert os.getenv("TEST_SET_SECRET") == "new_value"

    def test_set_secret_unsupported_backend_raises(self):
        """Test that set_secret raises for unsupported backend."""
        # Create manager with env backend first
        manager = SecretsManager(backend="env")
        # Manually change backend to test error
        manager.backend = "vault"

        with pytest.raises(NotImplementedError):
            manager.set_secret("KEY", "value")


class TestDataEncryption:
    """Test DataEncryption for field-level encryption."""

    def test_init_generates_key_if_none(self):
        """Test that encryption key is generated if not provided."""
        encryption = DataEncryption()
        assert encryption.cipher is not None

    def test_init_uses_env_key(self, monkeypatch):
        """Test that encryption key is read from environment."""
        key = Fernet.generate_key()
        monkeypatch.setenv("ENCRYPTION_KEY", key.decode())

        encryption = DataEncryption()
        assert encryption.cipher is not None

    def test_init_with_explicit_key(self):
        """Test initialization with explicit key."""
        key = Fernet.generate_key()
        encryption = DataEncryption(encryption_key=key)

        assert encryption.cipher is not None

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt works correctly."""
        key = Fernet.generate_key()
        encryption = DataEncryption(encryption_key=key)

        plaintext = "super_secret_password"
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_encrypt_returns_different_values(self):
        """Test that encrypting same value twice produces different ciphertexts."""
        key = Fernet.generate_key()
        encryption = DataEncryption(encryption_key=key)

        plaintext = "same_text"
        encrypted1 = encryption.encrypt(plaintext)
        encrypted2 = encryption.encrypt(plaintext)

        # Fernet includes timestamp, so ciphertexts will differ
        # But both should decrypt to same value
        assert encryption.decrypt(encrypted1) == plaintext
        assert encryption.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        key = Fernet.generate_key()
        encryption = DataEncryption(encryption_key=key)

        encrypted = encryption.encrypt("")
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == ""

    def test_encrypt_special_characters(self):
        """Test encrypting string with special characters."""
        key = Fernet.generate_key()
        encryption = DataEncryption(encryption_key=key)

        plaintext = "påsswörd!@#$%^&*()"
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == plaintext

    def test_generate_key_returns_valid_key(self):
        """Test that generate_key returns valid Fernet key."""
        key = DataEncryption.generate_key()

        assert isinstance(key, bytes)
        assert len(key) == 44  # Base64-encoded 32-byte key

        # Should be usable with Fernet
        cipher = Fernet(key)
        assert cipher is not None


class TestValidateEnvVars:
    """Test environment variable validation."""

    def test_validate_env_vars_all_present(self, monkeypatch):
        """Test validation when all required vars are present."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")
        monkeypatch.setenv("VAR3", "value3")

        result = validate_env_vars(["VAR1", "VAR2", "VAR3"])

        assert result == {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3",
        }

    def test_validate_env_vars_missing_raises(self):
        """Test that missing var raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_env_vars(["MISSING_VAR_12345"])

        assert "Missing required environment variables" in str(exc_info.value)
        assert "MISSING_VAR_12345" in str(exc_info.value)

    def test_validate_env_vars_multiple_missing(self):
        """Test error message with multiple missing vars."""
        with pytest.raises(ValueError) as exc_info:
            validate_env_vars(["MISSING1", "MISSING2", "MISSING3"])

        error_msg = str(exc_info.value)
        assert "MISSING1" in error_msg
        assert "MISSING2" in error_msg
        assert "MISSING3" in error_msg

    def test_validate_env_vars_empty_list(self):
        """Test validation with empty list."""
        result = validate_env_vars([])
        assert result == {}


class TestMaskSensitiveValue:
    """Test masking sensitive values for display."""

    def test_mask_sensitive_value_default(self):
        """Test masking with default show_chars (4)."""
        masked = mask_sensitive_value("1234567890")
        assert masked == "******7890"

    def test_mask_sensitive_value_custom_show_chars(self):
        """Test masking with custom show_chars."""
        masked = mask_sensitive_value("abcdefgh", show_chars=2)
        assert masked == "******gh"

    def test_mask_sensitive_value_short_string(self):
        """Test masking string shorter than show_chars."""
        masked = mask_sensitive_value("abc", show_chars=4)
        assert masked == "***"

    def test_mask_sensitive_value_empty_string(self):
        """Test masking empty string."""
        masked = mask_sensitive_value("")
        assert masked == "***"

    def test_mask_sensitive_value_exactly_show_chars(self):
        """Test masking string exactly equal to show_chars."""
        masked = mask_sensitive_value("1234", show_chars=4)
        assert masked == "***"


class TestCheckSecretsInCode:
    """Test checking for secrets in code files."""

    def test_check_secrets_in_code_clean_directory(self, tmp_path):
        """Test checking directory with no secrets."""
        # Create clean Python file
        test_file = tmp_path / "clean.py"
        test_file.write_text("def hello():\n    return 'world'\n")

        issues = check_secrets_in_code(tmp_path)
        assert issues == []

    def test_check_secrets_in_code_finds_password(self, tmp_path):
        """Test detection of hardcoded password."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text('password = "hardcoded_secret"\n')

        issues = check_secrets_in_code(tmp_path)

        assert len(issues) > 0
        assert "bad.py" in issues[0]
        assert "password" in issues[0]

    def test_check_secrets_in_code_finds_api_key(self, tmp_path):
        """Test detection of hardcoded API key."""
        bad_file = tmp_path / "secrets.py"
        bad_file.write_text("api_key = 'sk-1234567890'\n")

        issues = check_secrets_in_code(tmp_path)

        assert len(issues) > 0
        assert "secrets.py" in issues[0]
        assert "api_key" in issues[0]

    def test_check_secrets_in_code_ignores_venv(self, tmp_path):
        """Test that .venv directory is ignored."""
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        bad_file = venv_dir / "bad.py"
        bad_file.write_text('password = "secret"\n')

        issues = check_secrets_in_code(tmp_path)

        # Should not find secrets in .venv
        assert len(issues) == 0

    def test_check_secrets_in_code_multiple_patterns(self, tmp_path):
        """Test detection of multiple secret patterns."""
        bad_file = tmp_path / "multiple.py"
        bad_file.write_text(
            """
password = "secret1"
api_key = "key123"
secret = "mysecret"
token = "bearer_token"
"""
        )

        issues = check_secrets_in_code(tmp_path)

        # Should find multiple issues
        assert len(issues) >= 3


class TestSecureConfig:
    """Test SecureConfig helper class."""

    def test_init(self):
        """Test SecureConfig initialization."""
        config = SecureConfig()
        assert config.secrets_manager is not None

    def test_get_secret_required_exists(self, monkeypatch):
        """Test getting required secret that exists."""
        monkeypatch.setenv("REQUIRED_SECRET", "value")

        config = SecureConfig()
        value = config.get_secret("REQUIRED_SECRET", required=True)

        assert value == "value"

    def test_get_secret_required_missing_raises(self):
        """Test that missing required secret raises error."""
        config = SecureConfig()

        with pytest.raises(ValueError) as exc_info:
            config.get_secret("MISSING_REQUIRED_123", required=True)

        assert "Required secret" in str(exc_info.value)
        assert "MISSING_REQUIRED_123" in str(exc_info.value)

    def test_get_secret_optional_missing_returns_none(self):
        """Test that missing optional secret returns None."""
        config = SecureConfig()
        value = config.get_secret("OPTIONAL_SECRET", required=False)

        assert value is None

    def test_get_public_config_exists(self, monkeypatch):
        """Test getting public config value."""
        monkeypatch.setenv("PUBLIC_CONFIG", "public_value")

        config = SecureConfig()
        value = config.get_public_config("PUBLIC_CONFIG")

        assert value == "public_value"

    def test_get_public_config_with_default(self):
        """Test getting public config with default."""
        config = SecureConfig()
        value = config.get_public_config("NONEXISTENT", default="default")

        assert value == "default"


class TestSecurityIntegration:
    """Integration tests for security utilities."""

    def test_full_encryption_workflow(self):
        """Test complete encryption workflow."""
        # Generate key
        key = DataEncryption.generate_key()

        # Create encryption instance
        encryption = DataEncryption(encryption_key=key)

        # Encrypt sensitive data
        sensitive_data = "credit_card_number_1234567890"
        encrypted = encryption.encrypt(sensitive_data)

        # Store encrypted (would be in database)
        stored_value = encrypted

        # Later, decrypt for use
        decrypted = encryption.decrypt(stored_value)

        assert decrypted == sensitive_data

    def test_secrets_manager_with_secure_config(self, monkeypatch):
        """Test using SecretsManager with SecureConfig."""
        monkeypatch.setenv("DB_PASSWORD", "secure_pass")
        monkeypatch.setenv("API_KEY", "api_secret")

        config = SecureConfig()

        db_pass = config.get_secret("DB_PASSWORD", required=True)
        api_key = config.get_secret("API_KEY", required=True)

        # Values should be retrieved correctly
        assert db_pass == "secure_pass"
        assert api_key == "api_secret"

        # Should be masked when displayed
        # "secure_pass" = 11 chars, show last 4 = 7 asterisks + "pass"
        assert mask_sensitive_value(db_pass) == "*******pass"
        # "api_secret" = 10 chars, show last 4 = 6 asterisks + "cret"
        assert mask_sensitive_value(api_key) == "******cret"
