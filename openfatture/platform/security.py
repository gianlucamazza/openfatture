"""Input sanitization and validation for tool and CLI parameters.

Secrets are handled by :mod:`openfatture.platform.secrets` (OS keychain or a
private credentials file); log redaction lives in :mod:`openfatture.platform.logging`.
"""

import re


# Input sanitization functions for tool parameters
def sanitize_string_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is invalid or too long
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Remove null bytes and other control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)

    # Limit length to prevent DoS
    if len(sanitized) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    return sanitized.strip()


def sanitize_sql_like_input(value: str) -> str:
    """
    Sanitize string input for SQL LIKE queries.

    Args:
        value: Input string to sanitize

    Returns:
        Sanitized string safe for LIKE queries
    """
    # First apply general sanitization
    sanitized = sanitize_string_input(value, max_length=255)

    # Escape SQL LIKE wildcards
    sanitized = sanitized.replace("%", "\\%").replace("_", "\\_")

    return sanitized


def validate_integer_input(
    value: int, min_value: int | None = None, max_value: int | None = None
) -> int:
    """
    Validate integer input with bounds checking.

    Args:
        value: Integer value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        Validated integer

    Raises:
        ValueError: If input is invalid or out of bounds
    """
    if not isinstance(value, int):
        raise ValueError("Input must be an integer")

    if min_value is not None and value < min_value:
        raise ValueError(f"Value must be >= {min_value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"Value must be <= {max_value}")

    return value
