# Internationalization (i18n) Module

Modern multi-language support for OpenFatture using **Mozilla Fluent**.

## Supported Languages

- 🇮🇹 **Italian (it)** - Default locale
- 🇬🇧 **English (en)**
- 🇪🇸 **Spanish (es)**
- 🇫🇷 **French (fr)**
- 🇩🇪 **German (de)**

## Quick Start

```python
from openfatture.i18n import _, get_locale, set_locale

# Basic translation
message = _("common-yes")  # "Sì" (Italian default)

# With variables
invoice_msg = _("email-sdi-invio-subject", numero="001", anno=2024)
# "Invio Fattura 001/2024 a SDI"

# Change locale
set_locale("en")
message = _("common-yes")  # "Yes"

# Temporary locale switch
from openfatture.i18n.context import locale_context

with locale_context("fr"):
    message = _("common-yes")  # "Oui"
# Back to previous locale outside context
```

## Architecture

```
openfatture/i18n/
├── __init__.py          # Public API: _, get_locale(), set_locale()
├── loader.py            # FluentBundle loading and caching
├── translator.py        # Core _() function
├── formatters.py        # Currency, date, number formatters
├── context.py           # Context managers for locale switching
└── locales/
    ├── it/              # Italian (default)
    │   ├── common.ftl
    │   ├── email.ftl
    │   ├── cli.ftl
    │   ├── web.ftl
    │   └── errors.ftl
    ├── en/              # English
    ├── es/              # Spanish
    ├── fr/              # French
    └── de/              # German
```

## Fluent Translation List (.ftl) Format

Fluent uses a simple, powerful syntax for translations:

```fluent
# Simple message
common-yes = Yes

# Message with variable
email-sdi-invio-subject = Invoice { $numero }/{ $anno } Sent to SDI

# Pluralization
email-sdi-scarto-error-count = { $count ->
    [one] { $count } error detected
   *[other] { $count } errors detected
}

# With attributes
common-invoice =
    .singular = Invoice
    .plural = Invoices
```

## Configuration

Set locale via environment variable or Settings:

```bash
# Environment variable
export OPENFATTURE_LOCALE=en

# Or in .env file
OPENFATTURE_LOCALE=en
```

```python
# Or programmatically
from openfatture.utils.config import get_settings

settings = get_settings()
settings.locale = "en"
```

## Custom Formatters

The module provides locale-aware formatters for financial data:

```python
from openfatture.i18n.formatters import (
    format_euro,
    format_number,
    format_percentage,
    format_date_localized,
)

# Currency
format_euro(1234.56)           # "€ 1.234,56" (IT)
format_euro(1234.56, "en")     # "€1,234.56" (EN)

# Numbers
format_number(1234567.89)      # "1.234.567,89" (IT)

# Percentages
format_percentage(0.22)        # "22,00%" (IT)

# Dates
from datetime import date
format_date_localized(date(2024, 3, 15))           # "15 mar 2024" (IT)
format_date_localized(date(2024, 3, 15), "long", "en")  # "March 15, 2024"
```

## Translation Workflow

### 1. Add Message to .ftl File

Edit the appropriate .ftl file (e.g., `locales/it/cli.ftl`):

```fluent
cli-fattura-create-title = 🧾 Crea Nuova Fattura
cli-fattura-created = ✅ Fattura { $numero } creata con successo!
```

### 2. Translate to All Locales

Add the same message ID to all locale files:

```fluent
# locales/en/cli.ftl
cli-fattura-create-title = 🧾 Create New Invoice
cli-fattura-created = ✅ Invoice { $numero } created successfully!

# locales/es/cli.ftl
cli-fattura-create-title = 🧾 Crear Nueva Factura
cli-fattura-created = ✅ Factura { $numero } creada con éxito!
```

### 3. Use in Code

```python
from openfatture.i18n import _
from rich.console import Console

console = Console()
console.print(f"[bold blue]{_('cli-fattura-create-title')}[/bold blue]")
console.print(_("cli-fattura-created", numero="001"))
```

## Web UI (Streamlit) Integration

```python
import streamlit as st
from openfatture.i18n import _, get_locale, set_locale

# Locale selector in sidebar
locale = st.sidebar.selectbox(
    "🌐 Language",
    options=["it", "en", "es", "fr", "de"],
    index=["it", "en", "es", "fr", "de"].index(get_locale()),
)
if locale != get_locale():
    set_locale(locale)
    st.rerun()

# Use translations
st.title(_("web-dashboard-title"))
st.markdown(f"### {_('web-dashboard-metrics-title')}")
```

## AI Prompts Multi-Language

AI prompts are stored in separate files per locale:

```
openfatture/ai/prompts/
├── tax_advisor_it.yaml
├── tax_advisor_en.yaml
├── tax_advisor_es.yaml
├── tax_advisor_fr.yaml
└── tax_advisor_de.yaml
```

**Important**: Italian legal terms are preserved in all languages for accuracy:

```yaml
# tax_advisor_en.yaml
system_prompt: |
  You are an expert Italian tax consultant.

  Use these exact Italian terms:
  - IVA (VAT)
  - Ritenuta d'acconto (withholding tax)
  - Reverse charge (inversione contabile)

  Example: "Apply reverse charge (inversione contabile) per Article 17..."
```

## Error Messages

Localized exceptions:

```python
from openfatture.exceptions import LocalizedError

class PECNotConfiguredError(LocalizedError):
    message_key = "errors-pec-not-configured"

# Raises with localized message
raise PECNotConfiguredError()  # "Indirizzo PEC non configurato" (IT)
```

## Testing

```bash
# Run i18n completeness tests
uv run pytest tests/i18n/test_completeness.py -v

# Test specific locale
OPENFATTURE_LOCALE=en uv run pytest

# Check translation coverage
uv run python scripts/check_i18n_coverage.py
```

## Migration from Legacy Email i18n

Old JSON-based email translations are automatically migrated:

```python
# Old (openfatture/utils/email/i18n/it.json)
{
  "email": {
    "footer": {
      "generated_by": "Generato automaticamente da"
    }
  }
}

# New (openfatture/i18n/locales/it/email.ftl)
email-footer-generated-by = Generato automaticamente da
```

Use the migration script to convert old templates:

```bash
uv run python openfatture/i18n/migrations/email_json_to_ftl.py
```

## Best Practices

1. **Use kebab-case for message IDs**: `cli-fattura-create-title` ✅
2. **Namespace by module**: `cli-*`, `web-*`, `email-*`, `errors-*`
3. **Preserve Italian legal terms**: Always use "IVA", "reverse charge" + Italian translation
4. **Test all locales**: Ensure keys exist in all .ftl files
5. **Document variables**: Add comments in .ftl files for complex variables

## Performance

- **Bundle caching**: Fluent bundles are loaded once and cached
- **Thread-safe**: Uses thread-local storage for per-request locales
- **Fast lookups**: O(1) message lookup via FluentBundle

## Troubleshooting

**Missing translation warning**:
```
Translation not found: cli-fattura-new (locale: en)
```
→ Add the message ID to `locales/en/cli.ftl`

**Locale not changing**:
```python
# Ensure you're using set_locale(), not just updating Settings
set_locale("en")  # ✅
```

**Variables not interpolating**:
```fluent
# Wrong
cli-message = Invoice {numero}  # Missing $

# Correct
cli-message = Invoice { $numero }
```

## Contributing Translations

To add a new language:

1. Create directory: `openfatture/i18n/locales/pt/` (Portuguese example)
2. Copy .ftl files from `en/` as templates
3. Translate all messages
4. Add locale to `SUPPORTED_LOCALES` in `loader.py`
5. Add to `Settings.supported_locales` in `utils/config.py`
6. Run tests: `uv run pytest tests/i18n/ -v`

## References

- [Mozilla Fluent Syntax Guide](https://projectfluent.org/fluent/guide/)
- [Fluent Python Runtime](https://github.com/projectfluent/python-fluent)
- [Babel Documentation](https://babel.pocoo.org/)
