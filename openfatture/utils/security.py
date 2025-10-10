"""
Security utilities and secrets management.

Best practices 2025:
- Never log secrets
- Use environment variables
- Support external secrets managers (Vault, AWS Secrets Manager)
- Encrypt sensitive data at rest
"""

import os
from pathlib import Path

from cryptography.fernet import Fernet


class SecretsManager:
    """
    Secrets management with support for multiple backends.

    Supported backends:
    - Environment variables (default)
    - HashiCorp Vault (future)
    - AWS Secrets Manager (future)
    - Azure Key Vault (future)
    """

    def __init__(self, backend: str = "env") -> None:
        """
        Initialize secrets manager.

        Args:
            backend: Secrets backend to use (env, vault, aws, azure)
        """
        self.backend: str = backend

        if backend != "env":
            raise NotImplementedError(f"Backend '{backend}' not yet implemented")

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value.

        Args:
            key: Secret key name
            default: Default value if secret not found

        Returns:
            Secret value or default

        Note:
            Additional backends (Vault, AWS, Azure) can be added by:
            1. Adding backend-specific client initialization in __init__
            2. Adding elif branch here for the backend
            3. Using backend-specific secret retrieval methods
        """
        if self.backend == "env":
            value = os.getenv(key)
            return value if value is not None else default

        # Additional backends not yet implemented
        # Raise early to help developers identify missing backend support
        raise NotImplementedError(
            f"Backend '{self.backend}' not implemented. "
            f"Supported backends: 'env'. "
            f"To add support, implement get_secret() for '{self.backend}' backend."
        )

    def set_secret(self, key: str, value: str) -> None:
        """
        Set a secret value.

        Note: For production, use proper secrets management (not env vars).
        """
        if self.backend == "env":
            os.environ[key] = value
        else:
            raise NotImplementedError(f"Backend '{self.backend}' not implemented")


class DataEncryption:
    """
    Field-level encryption for sensitive data.

    Use this for encrypting PII/sensitive data before storing in database.
    """

    def __init__(self, encryption_key: bytes | None = None) -> None:
        """
        Initialize encryption.

        Args:
            encryption_key: Fernet encryption key (32 bytes, base64 encoded).
                          If None, reads from ENCRYPTION_KEY env var.
        """
        key_bytes: bytes
        if encryption_key is None:
            # Try to load from environment
            key_str = os.getenv("ENCRYPTION_KEY")
            if key_str:
                key_bytes = key_str.encode()
            else:
                # Generate a new key (NOT recommended for production)
                key_bytes = Fernet.generate_key()
        else:
            key_bytes = encryption_key

        self.cipher: Fernet = Fernet(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext
        """
        decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()


def validate_env_vars(required_vars: list[str]) -> dict[str, str]:
    """
    Validate that required environment variables are set.

    Args:
        required_vars: List of required variable names

    Returns:
        Dict of variable names to values

    Raises:
        ValueError: If any required variables are missing
    """
    missing: list[str] = []
    values: dict[str, str] = {}

    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing.append(var)
        else:
            values[var] = value

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them in your .env file or environment."
        )

    return values


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Mask sensitive value for display.

    Args:
        value: Value to mask
        show_chars: Number of characters to show at end

    Returns:
        Masked value (e.g., "***7890")
    """
    if not value or len(value) <= show_chars:
        return "***"

    return "*" * (len(value) - show_chars) + value[-show_chars:]


def check_secrets_in_code(directory: Path) -> list[str]:
    """
    Check for potential secrets in code files.

    This is a basic check - use proper tools like truffleHog for production.

    Args:
        directory: Directory to check

    Returns:
        List of potential issues found
    """
    issues: list[str] = []
    sensitive_patterns = [
        "password",
        "api_key",
        "secret",
        "token",
        "private_key",
    ]

    for py_file in directory.rglob("*.py"):
        if ".venv" in str(py_file) or "node_modules" in str(py_file):
            continue

        content = py_file.read_text(errors="ignore")
        for pattern in sensitive_patterns:
            if f'{pattern} = "' in content or f"{pattern} = '" in content:
                issues.append(f"{py_file}: Potential hardcoded {pattern}")

    return issues


# Example: Secure configuration helper
class SecureConfig:
    """
    Secure configuration that handles secrets properly.

    Usage:
        config = SecureConfig()
        pec_password = config.get_secret("PEC_PASSWORD")
    """

    def __init__(self) -> None:
        self.secrets_manager: SecretsManager = SecretsManager()

    def get_secret(self, key: str, required: bool = True) -> str | None:
        """Get a secret value."""
        value = self.secrets_manager.get_secret(key)

        if required and value is None:
            raise ValueError(
                f"Required secret '{key}' not found.\n"
                f"Please set it in your .env file or environment."
            )

        return value

    def get_public_config(self, key: str, default: str | None = None) -> str | None:
        """Get a non-sensitive configuration value."""
        return os.getenv(key, default)
