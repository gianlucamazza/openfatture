# Email Templates Documentation

## Overview

OpenFatture includes a professional email template system for SDI notifications, batch operations, and PEC communications. The system provides:

- **HTML + Plain Text** multipart emails
- **Internationalization** (Italian and English)
- **Responsive design** for mobile and desktop
- **Type-safe contexts** with Pydantic models
- **Automatic rate limiting** and retry logic

## Architecture

```
openfatture/utils/email/
├── models.py           # Pydantic context models
├── renderer.py         # Jinja2 template engine + i18n
├── sender.py           # TemplatePECSender (enhanced PEC sender)
├── styles.py           # CSS styles for emails
├── templates/          # HTML + text templates
│   ├── base.html/txt  # Base template with header/footer
│   ├── sdi/           # SDI notification templates (14 files)
│   ├── batch/         # Batch operation templates (2 files)
│   └── test/          # Test email templates (2 files)
└── i18n/
    ├── it.json        # Italian translations
    └── en.json        # English translations
```

## Quick Start

### 1. Configure Email Settings

Add to your `.env` file:

```env
# Email Branding
EMAIL_LOGO_URL=https://example.com/logo.png
EMAIL_PRIMARY_COLOR=#1976D2
EMAIL_SECONDARY_COLOR=#424242
EMAIL_FOOTER_TEXT=Custom footer text

# Email Notifications
NOTIFICATION_EMAIL=notify@example.com
NOTIFICATION_ENABLED=true

# Locale
LOCALE=it
```

### 2. Send Invoice to SDI

```python
from openfatture.utils.email.sender import TemplatePECSender
from openfatture.utils.config import get_settings

settings = get_settings()
sender = TemplatePECSender(settings=settings)

# Send invoice with professional template
success, error = sender.send_invoice_to_sdi(
    fattura=my_invoice,
    xml_path=Path("invoice.xml"),
    signed=True  # If digitally signed
)

if success:
    print("✅ Invoice sent to SDI")
else:
    print(f"❌ Error: {error}")
```

### 3. Test PEC Configuration

```python
sender = TemplatePECSender(settings=settings)

success, error = sender.send_test_email()

if success:
    print("✅ PEC configuration working!")
```

### 4. Automatic SDI Notifications

```python
from openfatture.sdi.notifiche.processor import NotificationProcessor

# Initialize with email sender for automatic notifications
sender = TemplatePECSender(settings=settings)
processor = NotificationProcessor(
    db_session=db_session,
    email_sender=sender  # Enable email notifications
)

# Process notification - automatically sends email
success, error, notification = processor.process_file(
    Path("RC_IT12345678901_00001.xml")
)
```

### 5. Batch Operation Summary

```python
from openfatture.core.batch.processor import BatchResult

result = BatchResult(total=100, start_time=datetime.now())
result.succeeded = 95
result.failed = 5
result.end_time = datetime.now()

sender = TemplatePECSender(settings=settings)
sender.send_batch_summary(
    result=result,
    operation_type="import",
    recipients=["admin@example.com"]
)
```

## Template Customization

### Override Templates

Create custom templates in your user directory:

```bash
~/.openfatture/templates/
└── sdi/
    └── invio_fattura.html  # Override default template
```

The renderer will automatically use your custom templates.

### Custom Branding

Create a custom branding configuration:

```python
from openfatture.utils.email.styles import EmailBranding

branding = EmailBranding(
    primary_color="#FF5722",  # Orange
    secondary_color="#212121",  # Dark gray
    success_color="#4CAF50",
    logo_url="https://mycompany.com/logo.png",
    footer_text="My Custom Footer"
)

renderer = TemplateRenderer(settings=settings, branding=branding)
```

## Available Templates

### SDI Templates

| Template | Description | Trigger |
|----------|-------------|---------|
| `sdi/invio_fattura` | Invoice submission to SDI | Manual send |
| `sdi/notifica_attestazione` | Transmission attestation (AT) | SDI accepts invoice |
| `sdi/notifica_consegna` | Delivery confirmation (RC) | Delivered to recipient |
| `sdi/notifica_scarto` | Rejection notification (NS) | SDI rejects invoice |
| `sdi/notifica_mancata_consegna` | Failed delivery (MC) | Cannot reach recipient |
| `sdi/notifica_esito_accettata` | Customer acceptance (NE-EC01) | Customer accepts |
| `sdi/notifica_esito_rifiutata` | Customer rejection (NE-EC02) | Customer rejects |

### Batch Templates

| Template | Description | Usage |
|----------|-------------|-------|
| `batch/riepilogo_batch` | Batch operation summary | Automatic after batch ops |

### Test Templates

| Template | Description | Usage |
|----------|-------------|-------|
| `test/test_email` | PEC configuration test | Manual testing |

## Internationalization

### Switch Locale

```python
sender = TemplatePECSender(settings=settings, locale="en")
```

### Add Custom Translations

Edit `openfatture/utils/email/i18n/it.json`:

```json
{
  "email": {
    "custom": {
      "my_key": "My custom text with {{placeholder}}"
    }
  }
}
```

Use in templates:

```jinja2
{{ _('email.custom.my_key', placeholder='value') }}
```

## Advanced Usage

### Preview Templates

Generate HTML preview without sending:

```python
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.models import FatturaInvioContext

renderer = TemplateRenderer(settings=settings)

context = FatturaInvioContext(
    fattura=my_invoice,
    cedente={...},
    destinatario="sdi@pec.it",
    is_signed=False,
    xml_filename="test.xml"
)

# Generate preview HTML file
preview_path = renderer.preview(
    template_name="sdi/invio_fattura.html",
    context=context,
    output_path=Path("/tmp/preview.html")
)

print(f"Preview: file://{preview_path}")
```

### Custom Rate Limiting

```python
from openfatture.utils.rate_limiter import RateLimiter

# Allow 5 emails per minute
custom_limiter = RateLimiter(max_calls=5, period=60)

sender = TemplatePECSender(
    settings=settings,
    rate_limit=custom_limiter,
    max_retries=5
)
```

### Manual Email Composition

```python
from openfatture.utils.email.models import EmailMessage, EmailAttachment

message = EmailMessage(
    subject="Custom Subject",
    html_body="<p>Custom HTML</p>",
    text_body="Custom text",
    recipients=["recipient@example.com"],
    attachments=[
        EmailAttachment(
            filename="document.pdf",
            content=pdf_bytes,
            mime_type="application/pdf"
        )
    ]
)

# Send manually
success, error = sender._send_email(message)
```

## Testing

### Unit Tests

Run the email template tests:

```bash
uv run python -m pytest tests/unit/test_email_templates.py -v
```

### Integration Testing

Test with real SMTP server:

```python
# Use test PEC account
settings.pec_address = "test@pec.example.com"
settings.pec_password = "test_password"
settings.notification_email = "test@example.com"

sender = TemplatePECSender(settings=settings)

# Send test email
success, error = sender.send_test_email()
assert success, f"Test failed: {error}"
```

## Troubleshooting

### Email Not Sending

1. **Check PEC credentials:**
   ```python
   print(f"PEC Address: {settings.pec_address}")
   print(f"SMTP Server: {settings.pec_smtp_server}:{settings.pec_smtp_port}")
   ```

2. **Test SMTP connection:**
   ```bash
   telnet smtp.pec.it 465
   ```

3. **Check rate limiting:**
   ```python
   wait_time = sender.rate_limiter.get_wait_time()
   print(f"Wait time: {wait_time}s")
   ```

### Template Not Found

```python
from pathlib import Path

templates_dir = Path(__file__).parent / "openfatture" / "utils" / "email" / "templates"
print(f"Templates directory: {templates_dir}")
print(f"Exists: {templates_dir.exists()}")
```

### Translations Missing

```python
renderer = TemplateRenderer(settings=settings, locale="it")
print(f"Translations: {renderer.translations.keys()}")
```

## Best Practices

1. **Always use templates** for consistency and maintainability
2. **Test with preview mode** before sending to real recipients
3. **Configure notification_email** for automatic SDI notifications
4. **Use rate limiting** to respect PEC server limits (default: 10/minute)
5. **Monitor failed sends** and implement retry queues for production
6. **Keep templates simple** - complex HTML may not render in all email clients
7. **Provide plain text fallback** - always render both HTML and text versions

## Performance

- **Template caching:** Jinja2 automatically caches compiled templates
- **Rate limiting:** Default 10 emails/minute prevents server overload
- **Retry logic:** Exponential backoff for transient errors (max 3 attempts)
- **Concurrent sends:** Use batch operations for multiple invoices

## Security

- **No credentials in templates:** All sensitive data passed via context
- **SMTP SSL/TLS:** Always uses encrypted connection
- **Input validation:** Pydantic models validate all context data
- **XSS protection:** Jinja2 auto-escaping enabled for HTML templates

## Future Enhancements

- Email tracking (open/click rates)
- PDF invoice attachments
- Calendar invites for payment deadlines
- Dark mode support
- Advanced charts in batch summaries
- Email queue with Celery for async sending

## Support

For issues or questions:
- GitHub: https://github.com/gianlucamazza/openfatture/issues
- Documentation: https://docs.openfatture.com
