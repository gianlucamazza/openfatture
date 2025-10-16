# OpenFatture Custom Commands Examples

This directory contains example custom commands that can be used with OpenFatture's interactive AI chat.

## Quick Start

1. **Copy commands to your config directory:**
   ```bash
   mkdir -p ~/.openfatture/commands/
   cp docs/examples/custom-commands/*.yaml ~/.openfatture/commands/
   ```

2. **Start interactive chat:**
   ```bash
   openfatture ai chat
   ```

3. **Use custom commands:**
   ```
   > /help          # Show all available commands
   > /custom        # List custom commands
   > /reload        # Reload commands after editing
   ```

## Available Example Commands

### 1. `/fattura-rapida` - Quick Invoice Creation
**Purpose**: Create a complete invoice with AI workflow in one command

**Usage:**
```
/fattura-rapida "Client Name" "Service Description" "Amount"
```

**Examples:**
```
/fattura-rapida "Acme Corp" "Web consulting 3h" "300"
/fr "Studio Legale Bianchi" "Sviluppo software custom" "2500"
```

**What it does:**
- Generates professional invoice description
- Suggests correct VAT rate and fiscal treatment
- Checks compliance with SDI regulations
- Creates invoice with confirmation

---

### 2. `/iva` - VAT Suggestion Shortcut
**Purpose**: Quick VAT rate and fiscal treatment suggestion

**Usage:**
```
/iva "Service Description" ["Client"] ["Amount"]
```

**Examples:**
```
/iva "IT consulting for construction company"
/vat "Formazione professionale" "Pubblica Amministrazione"
```

**What it does:**
- Analyzes service/product
- Suggests applicable VAT rate (0%, 4%, 10%, 22%)
- Identifies special regimes (reverse charge, split payment)
- Provides legal references (DPR 633/72)
- Suggests invoice notes

---

### 3. `/cliente-info` - Client Information Lookup
**Purpose**: Retrieve complete client information and statistics

**Usage:**
```
/cliente-info "Client Name or ID"
```

**Examples:**
```
/cliente-info "Rossi SRL"
/ci "12345678901"
/client 42
```

**What it does:**
- Shows complete client details (VAT, tax code, address)
- Invoice statistics (total, average, most recent)
- Payment status (paid, pending, overdue)
- Last 5 invoices
- Highlights critical issues (e.g., late payments)

---

### 4. `/report-mensile` - Monthly Business Report
**Purpose**: Generate comprehensive monthly report with statistics and analysis

**Usage:**
```
/report-mensile [Month] [Year]
```

**Examples:**
```
/report-mensile                  # Current month
/rm October 2025                 # Specific month
/monthly-report Settembre        # Italian month name
```

**What it does:**
- Invoicing metrics (total, count, average)
- Payment metrics (collected, pending, cash flow forecast)
- Top clients analysis
- Fiscal analysis (VAT, withholdings, stamps)
- Insights and recommendations

---

### 5. `/compliance-check` - Invoice Compliance Quick Check
**Purpose**: Verify invoice compliance before SDI submission

**Usage:**
```
/compliance-check "Invoice Number"
```

**Examples:**
```
/compliance-check "2025-042"
/cc 123
/verifica "FAT-2025-10-001"
```

**What it does:**
- Formal validation (required fields, formats)
- Invoice lines validation (descriptions, amounts)
- Fiscal treatment verification (VAT codes, reverse charge)
- SDI compliance (XML schema, known rejection patterns)
- Best practices check
- Provides acceptance probability (0-100%)

---

## Creating Your Own Custom Commands

### Command File Structure

Each command is defined in a YAML file with the following structure:

```yaml
name: my-command              # Command name (use in chat as /my-command)
description: Command description for help
category: general             # invoicing, tax, clients, reporting, compliance, general
aliases: [alias1, alias2]     # Alternative names
author: Your Name             # Optional
version: "1.0"                # Optional

template: |
  Your command template here.
  Use Jinja2 syntax for variables:
  - {{ arg1 }} - First positional argument
  - {{ arg2 }} - Second positional argument
  - {{ args }} - All arguments as list
  - {{ argN | default('default value') }} - With default

examples:
  - "/my-command arg1 arg2"
  - "/alias1 \"quoted argument\""
```

### Template Variables

- `{{ arg1 }}`, `{{ arg2 }}`, ... - Positional arguments (indexed from 1)
- `{{ args }}` - List of all arguments
- `{{ argN | default('value') }}` - Argument with default value
- `{{ argN | upper }}` - Apply Jinja2 filters (upper, lower, title, etc.)

### Tips for Writing Effective Commands

1. **Be Specific**: Provide clear structure and expected outputs
2. **Use Context**: Reference OpenFatture's domain (invoices, clients, VAT, SDI)
3. **Request Formatting**: Ask AI to format responses with tables, bullets, etc.
4. **Add Examples**: Include usage examples in the YAML
5. **Provide Defaults**: Use Jinja2 filters for optional parameters
6. **Test**: Use `/reload` to refresh commands after editing

### Example: Simple Custom Command

Create `~/.openfatture/commands/hello.yaml`:

```yaml
name: hello
description: Greet a person
category: general
aliases: [hi, ciao]

template: |
  Say hello to {{ arg1 | default('World') }} in a friendly way.
  Include an emoji and wish them a great day!

examples:
  - "/hello Alice"
  - "/hi"
```

Usage:
```
> /hello Bob
🔧 Custom command expanded:
Say hello to Bob in a friendly way...

🤖 AI:
Hello Bob! 👋 I hope you're having a wonderful day...
```

---

## Troubleshooting

### Command not found
- Check file is in `~/.openfatture/commands/`
- Verify YAML syntax is correct
- Use `/reload` to refresh registry
- Check `/custom` to see loaded commands

### Template expansion error
- Verify Jinja2 syntax (use `{{ variable }}` not `{ variable }`)
- Check for matching quotes in template
- Test with simple template first

### Command works but AI response is poor
- Make template more specific
- Add example outputs in template
- Request specific formatting (tables, bullets, etc.)
- Use domain terminology (fattura, cliente, IVA, SDI)

---

## Advanced Features

### Conditional Logic

```yaml
template: |
  Analyze service: {{ arg1 }}
  {% if arg2 %}
  For client: {{ arg2 }}
  {% endif %}
  {% if arg3 %}
  Amount: {{ arg3 }}€
  {% else %}
  (Amount not specified)
  {% endif %}
```

### Loops

```yaml
template: |
  Generate invoices for:
  {% for client in args %}
  - {{ client }}
  {% endfor %}
```

### Filters

```yaml
template: |
  Client: {{ arg1 | upper }}
  Service: {{ arg2 | title }}
  Amount: {{ arg3 | default('0') }}€
```

---

## Integration with OpenFatture

Custom commands have full access to AI capabilities:
- ✅ Tool calling (search invoices, clients)
- ✅ RAG enrichment (knowledge base, invoice history)
- ✅ Structured outputs
- ✅ Session persistence
- ✅ Cost tracking

The AI agent processes custom command expansions just like regular user input,
so you can leverage all OpenFatture features within your commands.

---

## Contributing

Have a useful custom command? Share it with the community:
1. Create a well-documented YAML file
2. Add usage examples
3. Submit a PR to the OpenFatture repository
4. Add to `docs/examples/custom-commands/`

---

## Support

- Documentation: https://github.com/gianlucamazza/openfatture
- Issues: https://github.com/gianlucamazza/openfatture/issues
- Discussions: https://github.com/gianlucamazza/openfatture/discussions
