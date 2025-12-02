# OpenFatture i18n Migration Guide

## Overview

This guide provides complete instructions for migrating OpenFatture CLI to a multi-language system using Fluent (`.ftl` files).

## Extract Files Generated

Three extraction files have been created:

1. **I18N_STRINGS_EXTRACTION.md** - Human-readable extraction with context and line references
2. **I18N_STRINGS_STRUCTURED.json** - Machine-parseable JSON format for tool integration
3. **I18N_MIGRATION_GUIDE.md** - This file with implementation guidance

## Extraction Summary

### Total Strings: 345+

| File | Help Strings | Console Output | Prompts | Tables | Total |
|------|-------------|----------------|---------|--------|-------|
| fattura.py | 12 | 42 | 12 | 5 | 71 |
| cliente.py | 9 | 9 | 13 | 3 | 34 |
| ai.py | 35 | 85+ | 5 | 10+ | 135+ |
| main.py | 3 | 1 | 0 | 0 | 4 |
| **TOTAL** | **59** | **137+** | **30** | **18+** | **244+** |

Note: ai.py has 200+ strings (file is 2400+ lines). Extraction focused on main commands.

## Implementation Steps

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 Add Fluent Dependency
```toml
# pyproject.toml
[project]
dependencies = [
    # ... existing dependencies
    "fluent.runtime>=0.4.0",  # Fluent runtime for translations
]
```

#### 1.2 Create i18n Module
```
openfatture/
├── i18n/
│   ├── __init__.py
│   ├── fluent_manager.py      # Fluent bundle initialization
│   ├── translator.py           # Translation lookup functions
│   └── locale_detector.py      # Locale detection from settings
└── locales/
    ├── en/
    │   ├── cli/
    │   │   ├── commands.ftl
    │   │   ├── fattura.ftl
    │   │   ├── cliente.ftl
    │   │   ├── ai.ftl
    │   │   └── main.ftl
    │   └── common.ftl
    ├── it/
    │   ├── cli/
    │   │   ├── commands.ftl
    │   │   ├── fattura.ftl
    │   │   ├── cliente.ftl
    │   │   ├── ai.ftl
    │   │   └── main.ftl
    │   └── common.ftl
    └── fr/
        ├── cli/
        │   └── ...
        └── common.ftl
```

#### 1.3 Fluent Manager Implementation
```python
# openfatture/i18n/fluent_manager.py
from fluent.runtime import FluentResourceLoader, FluentLocalization

class FluentManager:
    def __init__(self, default_locale="en", supported_locales=None):
        self.default_locale = default_locale
        self.supported_locales = supported_locales or ["en", "it"]
        self.bundles = {}
        self._load_bundles()

    def _load_bundles(self):
        loader = FluentResourceLoader("openfatture/locales/{locale}")
        for locale in self.supported_locales:
            self.bundles[locale] = FluentLocalization(
                [locale, self.default_locale],
                ["cli/commands.ftl", "cli/fattura.ftl", "cli/cliente.ftl",
                 "cli/ai.ftl", "cli/main.ftl", "common.ftl"],
                loader
            )

    def get_translation(self, locale, key, **kwargs):
        """Get translated string with variable substitution."""
        bundle = self.bundles.get(locale, self.bundles[self.default_locale])
        msg = bundle.get_message(key)
        if msg.value:
            return msg.value.format(**kwargs) if kwargs else msg.value
        return key  # Fallback to key if translation missing

    def t(self, locale, key, **kwargs):
        """Shorthand alias."""
        return self.get_translation(locale, key, **kwargs)

# Global manager instance
_manager = None

def get_fluent_manager():
    global _manager
    if _manager is None:
        from openfatture.utils.config import get_settings
        settings = get_settings()
        _manager = FluentManager(
            default_locale="en",
            supported_locales=["en", "it"]
        )
    return _manager
```

### Phase 2: Fluent File Creation (Week 1-2)

#### 2.1 Base Fluent Files Structure

Example: `openfatture/locales/en/cli/fattura.ftl`

```fluent
# Invoice creation strings
invoice-create-title = [bold blue]🧾 Create New Invoice[/bold blue]
invoice-no-clients-error = [red]No clients found. Add one first with 'cliente add'[/red]
invoice-available-clients = [cyan]Available clients:[/cyan]
invoice-client-selected = [green]✓ Client: { $client_name }[/green]
invoice-add-line-items-header = [bold]Add line items[/bold]
invoice-empty-description-hint = [dim]Enter empty description to finish[/dim]
invoice-item-added = [green]✓ Added: { $description } - €{ $total }[/green]
invoice-no-items-cancelled = [yellow]No items added. Invoice creation cancelled.[/yellow]
invoice-created-success = [bold green]✓ Invoice created successfully![/bold green]
invoice-select-client-prompt = Select client ID
invoice-number-prompt = Invoice number
invoice-date-prompt = Issue date (YYYY-MM-DD)
invoice-item-description-prompt = Item { $num } description
invoice-quantity-prompt = Quantity
invoice-unit-price-prompt = Unit price (€)
invoice-vat-rate-prompt = VAT rate (%)
invoice-ritenuta-confirm = Apply ritenuta d'acconto (withholding tax)?
invoice-ritenuta-rate-prompt = Ritenuta rate (%)
invoice-bollo-confirm = Add bollo (€2.00)?
invoice-delete-confirm = Delete invoice { $invoice_number }?
invoice-send-confirm = Send invoice to SDI now?
invoice-send-title = [bold blue]📤 Sending Invoice to SDI[/bold blue]
invoice-send-step-1 = [cyan]1. Generating XML...[/cyan]
invoice-xml-generated-step = [green]✓ XML generated[/green]
invoice-xml-generation-title = [bold blue]🔧 Generating FatturaPA XML[/bold blue]
invoice-xml-saved = [green]✓ XML saved to: { $path }[/green]
invoice-xml-generated-success = [green]✓ XML generated successfully![/green]
invoice-xml-preview = [dim]Preview (first 500 chars):[/dim]
invoice-sent-success = [green]✓ Invoice sent to SDI via PEC with professional template[/green]
invoice-send-complete = [bold green]✓ Invoice { $invoice_number } sent successfully![/bold green]
invoice-professional-email = [dim]📧 Professional email sent to SDI with:[/dim]
invoice-email-format = • HTML + plain text format
invoice-email-branding = • Company branding ({ $color })
invoice-email-language = • Language: { $locale }
invoice-notifications-header = [dim]📬 Automatic notifications:[/dim]
invoice-notification-email = • SDI responses will be emailed to: { $email }
invoice-monitor-pec = [dim]Monitor your PEC inbox for SDI notifications.[/dim]

# Table titles and columns
invoice-table-title = Invoice { $number }/{ $year }
invoice-table-invoices = Invoices ({ $count })
invoice-table-field = Field
invoice-table-value = Value
invoice-table-client = Client
invoice-table-date = Date
invoice-table-total = Total
invoice-table-status = Status
invoice-table-id = ID
invoice-table-number = Number
invoice-table-line-items = Line Items
invoice-table-qty = Qty
invoice-table-price = Price
invoice-table-vat = VAT%

# Help strings
fattura-help-cliente = Client ID
fattura-help-status = Filter by status
fattura-help-anno = Filter by year
fattura-help-limit = Max results
fattura-help-invoice-id = Invoice ID
fattura-help-force = Skip confirmation
fattura-help-output = Output path
fattura-help-no-validate = Skip XSD validation
fattura-help-pec = Send via PEC
```

Example: `openfatture/locales/it/cli/fattura.ftl`

```fluent
# Invoice creation strings
invoice-create-title = [bold blue]🧾 Crea Nuova Fattura[/bold blue]
invoice-no-clients-error = [red]Nessun cliente trovato. Aggiungine uno con 'cliente add'[/red]
invoice-available-clients = [cyan]Clienti disponibili:[/cyan]
invoice-client-selected = [green]✓ Cliente: { $client_name }[/green]
invoice-add-line-items-header = [bold]Aggiungi righe[/bold]
invoice-empty-description-hint = [dim]Inserisci una descrizione vuota per terminare[/dim]
invoice-item-added = [green]✓ Aggiunto: { $description } - €{ $total }[/green]
invoice-no-items-cancelled = [yellow]Nessuna riga aggiunta. Creazione fattura annullata.[/yellow]
invoice-created-success = [bold green]✓ Fattura creata con successo![/bold green]
invoice-select-client-prompt = Seleziona ID cliente
invoice-number-prompt = Numero fattura
invoice-date-prompt = Data emissione (YYYY-MM-DD)
invoice-item-description-prompt = Descrizione riga { $num }
invoice-quantity-prompt = Quantità
invoice-unit-price-prompt = Prezzo unitario (€)
invoice-vat-rate-prompt = Aliquota IVA (%)
invoice-ritenuta-confirm = Applicare ritenuta d'acconto?
invoice-ritenuta-rate-prompt = Aliquota ritenuta (%)
invoice-bollo-confirm = Aggiungere bollo (€2.00)?
invoice-delete-confirm = Eliminare fattura { $invoice_number }?
invoice-send-confirm = Inviare fattura all'SDI ora?
invoice-send-title = [bold blue]📤 Invio Fattura all'SDI[/bold blue]
invoice-send-step-1 = [cyan]1. Generazione XML...[/cyan]
invoice-xml-generated-step = [green]✓ XML generato[/green]
invoice-xml-generation-title = [bold blue]🔧 Generazione FatturaPA XML[/bold blue]
invoice-xml-saved = [green]✓ XML salvato in: { $path }[/green]
invoice-xml-generated-success = [green]✓ XML generato con successo![/green]
invoice-xml-preview = [dim]Anteprima (primi 500 caratteri):[/dim]
invoice-sent-success = [green]✓ Fattura inviata all'SDI via PEC con template professionale[/green]
invoice-send-complete = [bold green]✓ Fattura { $invoice_number } inviata con successo![/bold green]
invoice-professional-email = [dim]📧 Email professionale inviata all'SDI con:[/dim]
invoice-email-format = • Formato HTML + testo semplice
invoice-email-branding = • Branding aziendale ({ $color })
invoice-email-language = • Lingua: { $locale }
invoice-notifications-header = [dim]📬 Notifiche automatiche:[/dim]
invoice-notification-email = • Le risposte dell'SDI verranno inviate a: { $email }
invoice-monitor-pec = [dim]Monitora la tua casella PEC per le notifiche SDI.[/dim]

# Table titles and columns
invoice-table-title = Fattura { $number }/{ $year }
invoice-table-invoices = Fatture ({ $count })
invoice-table-field = Campo
invoice-table-value = Valore
invoice-table-client = Cliente
invoice-table-date = Data
invoice-table-total = Totale
invoice-table-status = Stato
invoice-table-id = ID
invoice-table-number = Numero
invoice-table-line-items = Righe
invoice-table-qty = Qty
invoice-table-price = Prezzo
invoice-table-vat = IVA%

# Help strings
fattura-help-cliente = ID Cliente
fattura-help-status = Filtra per stato
fattura-help-anno = Filtra per anno
fattura-help-limit = Numero massimo risultati
fattura-help-invoice-id = ID Fattura
fattura-help-force = Ignora conferma
fattura-help-output = Percorso output
fattura-help-no-validate = Ignora validazione XSD
fattura-help-pec = Invia via PEC
```

### Phase 3: Code Integration (Week 2-3)

#### 3.1 Update CLI Commands

```python
# openfatture/cli/commands/fattura.py - BEFORE
console.print("\n[bold blue]🧾 Create New Invoice[/bold blue]\n")
console.print("[red]No clients found. Add one first with 'cliente add'[/red]")

# AFTER
from openfatture.i18n.fluent_manager import get_fluent_manager

def crea_fattura(cliente_id: int | None = typer.Option(None, "--cliente", help="Client ID")):
    # Get locale from settings
    settings = get_settings()
    locale = settings.locale  # "en" or "it"

    # Get fluent manager
    fm = get_fluent_manager()

    # Use translations
    title = fm.t(locale, "invoice-create-title")
    console.print(f"\n{title}\n")

    no_clients_msg = fm.t(locale, "invoice-no-clients-error")
    console.print(no_clients_msg)
```

#### 3.2 Create Translation Helper

```python
# openfatture/i18n/translator.py
from openfatture.utils.config import get_settings
from openfatture.i18n.fluent_manager import get_fluent_manager

def t(key: str, **kwargs) -> str:
    """
    Translate string using current locale from settings.

    Usage:
        msg = t("invoice-create-title")
        msg = t("invoice-item-added", description="Web dev", total=100)
    """
    settings = get_settings()
    locale = settings.locale or "en"
    fm = get_fluent_manager()
    return fm.t(locale, key, **kwargs)

def t_locale(key: str, locale: str, **kwargs) -> str:
    """Translate string using explicit locale."""
    fm = get_fluent_manager()
    return fm.t(locale, key, **kwargs)
```

#### 3.3 Update Settings for Locale

```python
# openfatture/utils/config.py - add to Settings class
class Settings(BaseSettings):
    # ... existing fields ...

    locale: str = Field(
        default="en",
        description="UI locale (en, it, fr, ...)",
        validation_alias="OPENFATTURE_LOCALE",
    )

    supported_locales: list[str] = Field(
        default=["en", "it"],
        description="Supported locales",
    )
```

### Phase 4: Testing & Validation (Week 3)

#### 4.1 Unit Tests for Translations

```python
# tests/i18n/test_fluent_manager.py
import pytest
from openfatture.i18n.fluent_manager import get_fluent_manager

def test_fluent_manager_english():
    fm = get_fluent_manager()
    text = fm.t("en", "invoice-create-title")
    assert "Create New Invoice" in text
    assert "🧾" in text

def test_fluent_manager_italian():
    fm = get_fluent_manager()
    text = fm.t("it", "invoice-create-title")
    assert "Crea Nuova Fattura" in text
    assert "🧾" in text

def test_fluent_variable_substitution():
    fm = get_fluent_manager()
    text = fm.t("en", "invoice-item-added",
                description="Consulting", total=100)
    assert "Consulting" in text
    assert "100" in text

def test_fallback_to_english():
    fm = get_fluent_manager()
    # French not yet translated - should fallback to English
    text = fm.t("fr", "invoice-create-title")
    assert "Create New Invoice" in text or "Crea Nuova Fattura" in text
```

#### 4.2 CLI Integration Tests

```python
# tests/cli/test_i18n_integration.py
def test_fattura_commands_english(monkeypatch):
    """Test that fattura commands use English translations."""
    monkeypatch.setenv("OPENFATTURE_LOCALE", "en")
    # Run fattura crea command and verify English strings in output

def test_fattura_commands_italian(monkeypatch):
    """Test that fattura commands use Italian translations."""
    monkeypatch.setenv("OPENFATTURE_LOCALE", "it")
    # Run fattura crea command and verify Italian strings in output
```

### Phase 5: Documentation & Deployment (Week 4)

#### 5.1 Create i18n Developer Guide

```markdown
# i18n Development Guide

## Adding New Translations

1. Add string ID and English text to `locales/en/cli/{module}.ftl`
2. Add same ID with Italian translation to `locales/it/cli/{module}.ftl`
3. Update code to use `t("string-id")` instead of hardcoded strings

## String ID Naming Convention

- Start with module name: `fattura-`, `cliente-`, `ai-`
- Use lowercase with hyphens: `invoice-create-title`
- Group by type: `help-`, `prompt-`, `error-`, `success-`
- Include context: `client-id-help` vs `client-id-error`

## Testing Translations

```bash
OPENFATTURE_LOCALE=en uv run pytest tests/i18n/
OPENFATTURE_LOCALE=it uv run pytest tests/i18n/
```

## Adding New Locales

1. Create directory: `openfatture/locales/{locale_code}/cli/`
2. Copy English `.ftl` files as template
3. Translate all strings (key names stay the same)
4. Add locale to `Settings.supported_locales`
5. Test with: `OPENFATTURE_LOCALE={locale_code} pytest`
```

#### 5.2 Add Locale Environment Variable to .env.example

```bash
# Language / Locale
OPENFATTURE_LOCALE=en  # Supported: en, it
```

## Migration Checklist

### Phase 1: Infrastructure ✓
- [ ] Add fluent.runtime dependency to pyproject.toml
- [ ] Create `openfatture/i18n/` module structure
- [ ] Implement FluentManager
- [ ] Create directory structure for `.ftl` files

### Phase 2: Content Creation ✓
- [ ] Create English Fluent files (en/*.ftl)
- [ ] Create Italian Fluent files (it/*.ftl)
- [ ] Validate Fluent syntax
- [ ] Test variable substitution

### Phase 3: Code Integration
- [ ] Update fattura.py commands
- [ ] Update cliente.py commands
- [ ] Update ai.py commands (prioritize main commands)
- [ ] Update main.py help strings
- [ ] Add i18n imports and translator function calls
- [ ] Remove hardcoded strings

### Phase 4: Testing
- [ ] Unit tests for FluentManager
- [ ] Integration tests for each command
- [ ] Test locale switching
- [ ] Test fallback behavior
- [ ] Test variable substitution

### Phase 5: Documentation
- [ ] Create i18n developer guide
- [ ] Document string ID naming convention
- [ ] Document how to add new locales
- [ ] Update CLI help with locale information
- [ ] Add i18n section to CLAUDE.md

## Rollout Strategy

### Recommendation: Phased Rollout by Module

1. **Week 1-2: fattura.py** (72 strings)
   - Higher usage, well-defined commands
   - Easier to test invoice workflows

2. **Week 2-3: cliente.py** (34 strings)
   - Similar complexity to fattura
   - Quick win for consistency

3. **Week 3-4: main.py + selected ai.py** (50 strings)
   - Help strings and main AI commands
   - Leave advanced AI commands for later

4. **Week 4-5: Remaining ai.py** (100+ strings)
   - Largest module but can be done incrementally
   - Focus on most-used commands first

## Resource Estimates

| Phase | Effort | Duration | Dependencies |
|-------|--------|----------|--------------|
| Infrastructure | 4-6 hrs | 1-2 days | Fluent knowledge |
| Content Creation | 8-10 hrs | 2-3 days | Translation expertise |
| Code Integration | 12-16 hrs | 3-4 days | Infrastructure complete |
| Testing | 8-12 hrs | 2-3 days | Integration complete |
| Documentation | 4-6 hrs | 1-2 days | All code done |
| **TOTAL** | **36-50 hrs** | **2-3 weeks** | Sequential |

## Future Enhancements

1. **Additional Languages**
   - Spanish (es): `openfatture/locales/es/`
   - French (fr): `openfatture/locales/fr/`
   - German (de): `openfatture/locales/de/`

2. **Locale Auto-Detection**
   - Detect from system locale (os.environ["LANG"])
   - Allow override via command-line flag: `--locale it`
   - Store user preference

3. **Translation Management**
   - Use Crowdin or POEditor for community translations
   - Automated workflow for syncing translations
   - Translation completeness dashboard

4. **Right-to-Left (RTL) Support**
   - If adding Arabic, Hebrew, etc.
   - Requires UI layout adjustments

5. **Contextual Translations**
   - Different messages for different user roles
   - Formal vs informal registers
   - Regional variants (Latin American Spanish vs Spain Spanish)

## References

- [Fluent Documentation](https://projectfluent.org/)
- [fluent.runtime Python Docs](https://fluent-react.readthedocs.io/)
- [FTL Syntax Guide](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf)
- [CLDR Plural Rules](http://cldr.unicode.org/index/cldr-spec/plural-rules)

## Approval & Rollout

- [ ] Technical review: Architecture sound?
- [ ] Content review: Translations accurate?
- [ ] QA review: All strings covered?
- [ ] Product review: UX feels natural?
- [ ] Merge to main and deploy
