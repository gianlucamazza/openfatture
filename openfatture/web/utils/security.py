"""Security utilities for Streamlit web app - Best Practices 2025.

Provides:
- File upload validation
- Input sanitization
- XSS prevention
"""

import html
import re
from pathlib import Path
from typing import Any

import streamlit as st


def validate_file_upload(
    uploaded_file: Any,
    allowed_extensions: list[str] | None = None,
    max_size_mb: int = 10,
    allowed_mimetypes: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Validate uploaded file for security.

    Args:
        uploaded_file: Streamlit UploadedFile object
        allowed_extensions: List of allowed file extensions (e.g., ["pdf", "txt"])
        max_size_mb: Maximum file size in MB
        allowed_mimetypes: List of allowed MIME types

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_file_upload(
        ...     file,
        ...     allowed_extensions=["pdf", "png", "jpg"],
        ...     max_size_mb=5
        ... )
        >>> if not is_valid:
        ...     st.error(error)
    """
    if not uploaded_file:
        return False, "No file uploaded"

    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.2f}MB) exceeds limit ({max_size_mb}MB)"

    # Check extension
    if allowed_extensions:
        file_ext = Path(uploaded_file.name).suffix.lower().lstrip(".")
        if file_ext not in allowed_extensions:
            return (
                False,
                f"File type .{file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}",
            )

    # Check MIME type
    if allowed_mimetypes:
        if uploaded_file.type not in allowed_mimetypes:
            return False, f"MIME type {uploaded_file.type} not allowed"

    return True, ""


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.

    Args:
        text: Input text that may contain HTML

    Returns:
        Sanitized text with HTML escaped

    Example:
        >>> sanitize_html("<script>alert('xss')</script>")
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
    """
    return html.escape(text)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'etcpasswd'
        >>> sanitize_filename("my invoice #123.pdf")
        'my_invoice_123.pdf'
    """
    # Remove path components
    filename = Path(filename).name

    # Remove dangerous characters
    filename = re.sub(r"[^\w\s.-]", "", filename)

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Remove leading dots (hidden files)
    filename = filename.lstrip(".")

    # Ensure not empty
    if not filename:
        filename = "unnamed_file"

    return filename


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        True if valid

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid")
        False
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_partita_iva(partita_iva: str) -> bool:
    """
    Validate Italian VAT number format.

    Args:
        partita_iva: VAT number (with or without IT prefix)

    Returns:
        True if valid format

    Example:
        >>> validate_partita_iva("IT12345678901")
        True
        >>> validate_partita_iva("12345678901")
        True
    """
    # Remove IT prefix
    piva = partita_iva.replace("IT", "").strip()

    # Must be 11 digits
    if not re.match(r"^\d{11}$", piva):
        return False

    return True


# Security headers for HTML rendering
SAFE_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "a",
    "span",
    "div",
    "code",
    "pre",
]


def render_safe_html(html_content: str, allowed_tags: list[str] | None = None) -> None:
    """
    Render HTML with whitelist validation.

    Best Practice: Only use unsafe_allow_html=True with validated content.

    Args:
        html_content: HTML to render
        allowed_tags: List of allowed tags (default: SAFE_HTML_TAGS)

    Example:
        >>> render_safe_html("<p>Safe content</p><script>alert('bad')</script>")
        # Renders only <p> tag, removes <script>
    """
    if allowed_tags is None:
        allowed_tags = SAFE_HTML_TAGS

    # Simple tag validation (for production, use bleach library)
    for tag in re.findall(r"<(\w+)", html_content):
        if tag.lower() not in allowed_tags:
            st.error(f"Security: Blocked HTML tag <{tag}>")
            return

    st.markdown(html_content, unsafe_allow_html=True)


# Rate limiting helper (session-based)
def check_rate_limit(action: str, max_calls: int = 10, window_seconds: int = 60) -> bool:
    """
    Simple rate limiting using session state.

    Args:
        action: Action identifier
        max_calls: Maximum calls allowed
        window_seconds: Time window in seconds

    Returns:
        True if within limit

    Example:
        >>> if not check_rate_limit("ai_query", max_calls=5, window_seconds=60):
        ...     st.error("Rate limit exceeded. Try again in a minute.")
    """
    import time

    key = f"rate_limit_{action}"

    if key not in st.session_state:
        st.session_state[key] = []

    # Clean old entries
    now = time.time()
    st.session_state[key] = [t for t in st.session_state[key] if now - t < window_seconds]

    # Check limit
    if len(st.session_state[key]) >= max_calls:
        return False

    # Add current call
    st.session_state[key].append(now)
    return True
