# Security Integration Guide - Task 8

## Overview

This guide documents the security improvements implemented as part of the Streamlit Best Practices 2025 initiative (Task 8: Security improvements).

## Security Utilities Created

**File**: `openfatture/web/utils/security.py`

### Functions Implemented:

1. **`validate_file_upload()`** - File upload validation
   - Validates file extensions
   - Checks file size (configurable max MB)
   - Validates MIME types
   - Returns tuple: `(is_valid: bool, error_message: str)`

2. **`sanitize_html()`** - XSS prevention
   - Escapes HTML special characters
   - Prevents script injection

3. **`sanitize_filename()`** - Path traversal prevention
   - Removes path components (../, etc.)
   - Strips dangerous characters
   - Removes leading dots (hidden files)

4. **`validate_email()`** - Email format validation
   - Regex-based validation
   - Returns bool

5. **`validate_partita_iva()`** - Italian VAT number validation
   - Handles IT prefix
   - Validates 11-digit format

6. **`render_safe_html()`** - Safe HTML rendering
   - Whitelist-based tag validation
   - Blocks unauthorized tags

7. **`check_rate_limit()`** - Session-based rate limiting
   - Configurable max calls and time window
   - Uses st.session_state for tracking
   - Returns bool (within limit or not)

## Integration Points

### 1. AI Assistant Page - File Upload (IN PROGRESS)

**File**: `openfatture/web/pages/5_🤖_AI_Assistant.py`

**Location**: Line ~263 (File upload section)

**Required Changes**:
```python
# BEFORE:
if uploaded_file:
    file_details = {
        "name": uploaded_file.name,
        "type": uploaded_file.type,
        "size": uploaded_file.size,
    }
    st.success(f"📄 File caricato...")
    # ... store in session state

# AFTER (with security):
if uploaded_file:
    # Security validation (Best Practice 2025)
    is_valid, error_msg = validate_file_upload(
        uploaded_file,
        allowed_extensions=["pdf", "txt", "md", "png", "jpg", "jpeg"],
        max_size_mb=10,
        allowed_mimetypes=[
            "application/pdf",
            "text/plain",
            "text/markdown",
            "image/png",
            "image/jpeg",
        ],
    )

    if not is_valid:
        st.error(f"⚠️ {error_msg}")
    else:
        file_details = {
            "name": uploaded_file.name,
            "type": uploaded_file.type,
            "size": uploaded_file.size,
        }
        st.success(f"📄 File caricato...")
        # ... store in session state
```

### 2. AI Assistant Page - Rate Limiting

**File**: `openfatture/web/pages/5_🤖_AI_Assistant.py`

**Location**: Line ~332 (Chat input processing)

**Required Changes**:
```python
if user_input:
    # Rate limiting (Best Practice 2025: prevent abuse)
    if not check_rate_limit("ai_chat", max_calls=10, window_seconds=60):
        st.error("⏱️ Limite di richieste raggiunto. Riprova tra un minuto.")
        st.stop()

    # Handle slash commands first
    expanded_message, command_feedback = handle_slash_command(...)
    # ... rest of chat processing
```

### 3. Client Management Page - Input Validation

**File**: `openfatture/web/pages/3_👥_Clienti.py`

**Required Changes**:
```python
# When creating/editing clients
if partita_iva:
    if not validate_partita_iva(partita_iva):
        st.error("⚠️ Partita IVA non valida (deve essere 11 cifre)")

if email:
    if not validate_email(email):
        st.error("⚠️ Formato email non valido")
```

### 4. Invoice Creation - Filename Sanitization

**File**: `openfatture/web/services/invoice_service.py`

**Required Changes**:
```python
from openfatture.web.utils.security import sanitize_filename

def generate_xml_filename(invoice_number: str, cliente_name: str) -> str:
    # Sanitize inputs to prevent path traversal
    safe_number = sanitize_filename(invoice_number)
    safe_cliente = sanitize_filename(cliente_name)
    return f"{safe_number}_{safe_cliente}.xml"
```

## Benefits

1. **File Upload Security**:
   - Prevents malicious file uploads
   - Limits file size to prevent DoS
   - Validates MIME types to prevent disguised files

2. **Rate Limiting**:
   - Prevents AI API abuse
   - Protects against accidental loops
   - Reduces cost overruns

3. **Input Validation**:
   - Prevents invalid data entry
   - Improves user experience with instant feedback
   - Ensures data integrity

4. **XSS Prevention**:
   - Protects against code injection
   - Safe HTML rendering with whitelists
   - Sanitized filename storage

## Testing

**File**: `tests/web/utils/test_security.py` (TO BE CREATED)

```python
def test_validate_file_upload_success():
    """Test valid file upload passes validation."""
    # ... test implementation

def test_validate_file_upload_size_exceeded():
    """Test file size limit enforcement."""
    # ... test implementation

def test_validate_file_upload_invalid_extension():
    """Test extension validation."""
    # ... test implementation

def test_sanitize_html_prevents_xss():
    """Test HTML sanitization."""
    # ... test implementation

def test_check_rate_limit_enforcement():
    """Test rate limiting logic."""
    # ... test implementation
```

## Status

- ✅ Security utilities module created
- ⏸️ AI Assistant integration (file modification conflicts)
- ⏳ Pending: Client page validation
- ⏳ Pending: Invoice filename sanitization
- ⏳ Pending: Unit tests creation

## Next Steps

1. Wait for AI Assistant page modifications to stabilize
2. Apply file upload validation changes
3. Apply rate limiting changes
4. Create comprehensive unit tests
5. Integration test with actual file uploads
6. Document in user-facing docs

## References

- OWASP File Upload Security: https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload
- Streamlit Security Best Practices: https://docs.streamlit.io/develop/concepts/architecture/security
- OWASP XSS Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
