# PDF Invoice Generation

**Professional PDF generation for Italian electronic invoices with legal compliance.**

> **📦 Module**: `openfatture.services.pdf`
> **Engine**: ReportLab 4.0+
> **Status**: ✅ Production-ready (implemented in Phase 3)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Templates](#templates)
5. [Configuration](#configuration)
6. [Components](#components)
7. [QR Code Integration](#qr-code-integration)
8. [PDF/A Compliance](#pdfa-compliance)
9. [CLI Commands](#cli-commands)
10. [Python API](#python-api)
11. [Customization](#customization)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

OpenFatture's **PDF Generation** module creates professional, legally-compliant PDF invoices from FatturaPA XML data. Perfect for sending human-readable invoices to clients alongside the official XML.

### Why PDF Generation?

- **Client-Friendly**: Not all clients can read XML files
- **Professional Presentation**: Beautiful, branded invoices
- **Legal Archiving**: PDF/A-3 compliance for 10-year storage
- **Payment Facilitation**: Integrated QR codes for instant payment
- **Print-Ready**: High-quality output for printing

### Key Features

✅ **3 Professional Templates** - Minimalist, Professional, Branded
✅ **PDF/A-3 Compliance** - Legal archiving (Agenzia delle Entrate approved)
✅ **QR Code Support** - SEPA instant payment (pagoPa planned)
✅ **Automatic Pagination** - Multi-page invoices handled automatically
✅ **Reusable Components** - Modular design for easy customization
✅ **Type-Safe Config** - Pydantic-based configuration
✅ **Italian Standards** - Full FatturaPA compliance

---

## Features

### 1. Multiple Templates

Choose from 3 professionally-designed templates:

| Template | Best For | Customization | File Size |
|----------|----------|---------------|-----------|
| **Minimalist** | Freelancers, startups | Low | ~50 KB |
| **Professional** | SMBs, service companies | Medium | ~80 KB |
| **Branded** | Enterprises, agencies | High | ~120 KB |

### 2. Reusable Components

Modular components for consistent design:

- **Header** - Company logo, name, VAT, address
- **Footer** - Page numbers, digital signature note, custom text
- **Table** - Invoice lines with automatic wrapping
- **QR Code** - Payment QR codes (SEPA, pagoPa)

### 3. Legal Compliance

- **PDF/A-3** - ISO 19005-3 for 10-year archiving
- **FatturaPA Integration** - All data from XML
- **Digital Signature Support** - Notes for P7M signatures
- **Metadata** - Complete PDF metadata (author, title, subject)

### 4. Payment Integration

- **QR Codes** - SEPA EPC QR for instant bank transfers
- **pagoPa** - Italian public administration payment system (planned)
- **IBAN Display** - Clear payment instructions
- **Payment Terms** - Due dates and conditions

---

## Quick Start

### Installation

PDF generation is included with OpenFatture. Ensure `reportlab` is installed:

```bash
uv sync --all-extras
```

### Basic Usage

```python
from openfatture.services.pdf import PDFGenerator, PDFGeneratorConfig
from openfatture.storage.database import get_session
from openfatture.storage.database.models import Fattura

# 1. Configure generator
config = PDFGeneratorConfig(
    template="professional",
    company_name="ACME S.r.l.",
    company_vat="12345678901",
    company_address="Via Roma 123",
    company_city="Milano, 20100 MI",
    logo_path="./logo.png",
    enable_qr_code=True
)

# 2. Create generator
generator = PDFGenerator(config)

# 3. Load invoice from database
with get_session() as session:
    fattura = session.query(Fattura).filter_by(numero=1, anno=2025).first()

    # 4. Generate PDF
    pdf_path = generator.generate(fattura, output_path="fattura_001_2025.pdf")

print(f"✓ PDF generated: {pdf_path}")
```

### CLI Usage

```bash
# Generate PDF for invoice
openfatture pdf generate 123 --template professional --output fattura.pdf

# Generate with QR code
openfatture pdf generate 123 --qr-code --output fattura.pdf

# Generate for all invoices in 2025
openfatture pdf batch --year 2025 --template branded --output-dir ./pdfs/

# Test template
openfatture pdf preview --template minimalist
```

---

## Templates

### 1. Minimalist Template

**Best for**: Freelancers, startups, simple invoices

**Features**:
- Clean, single-color design (#2C3E50)
- No logo required
- Minimal graphics, maximum readability
- Fast generation (~50KB files)
- Mobile-friendly layout

**Preview**:
```
┌────────────────────────────────────────┐
│ YOUR COMPANY NAME                      │
│ P.IVA: 12345678901                     │
│ Via Roma 123, Milano                   │
├────────────────────────────────────────┤
│                                        │
│ FATTURA N. 001/2025                    │
│ Data: 01/10/2025                       │
│                                        │
│ Cliente: Mario Rossi SRL               │
│ P.IVA: 98765432109                     │
│                                        │
├────────────────────────────────────────┤
│ Descrizione        Qta  Prezzo  Totale│
├────────────────────────────────────────┤
│ Consulenza IT        8  100.00  800.00│
│ Sviluppo software    4  150.00  600.00│
├────────────────────────────────────────┤
│                      IMPONIBILE  1400.00│
│                      IVA 22%      308.00│
│                      TOTALE      1708.00│
└────────────────────────────────────────┘
```

**Usage**:
```python
config = PDFGeneratorConfig(template="minimalist")
generator = PDFGenerator(config)
```

### 2. Professional Template

**Best for**: SMBs, service companies, consultants

**Features**:
- Company logo support (top-left)
- Two-color design (primary + accent)
- Professional typography
- Client section with borders
- IBAN + payment terms
- Medium file size (~80KB)

**Preview**:
```
┌────────────────────────────────────────┐
│ [LOGO]  YOUR COMPANY NAME              │
│         P.IVA: 12345678901             │
│         Via Roma 123, Milano, MI       │
│         ☎ +39 02 1234567               │
│         @ info@yourcompany.it          │
├────────────────────────────────────────┤
│                                        │
│ ┌─────────────────────────────────┐   │
│ │ FATTURA N. 001/2025             │   │
│ │ Data Emissione: 01/10/2025      │   │
│ │ Scadenza: 31/10/2025            │   │
│ └─────────────────────────────────┘   │
│                                        │
│ ┌─────────────────────────────────┐   │
│ │ CLIENTE                         │   │
│ │ Mario Rossi SRL                 │   │
│ │ P.IVA: 98765432109              │   │
│ │ Via Milano 456, Roma, RM        │   │
│ └─────────────────────────────────┘   │
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ Descrizione  Qta Prezzo   Totale │  │
│ ├──────────────────────────────────┤  │
│ │ Consulenza IT  8 100.00   800.00 │  │
│ ├──────────────────────────────────┤  │
│ │              IMPONIBILE  1400.00 │  │
│ │              IVA 22%      308.00 │  │
│ │              TOTALE      1708.00 │  │
│ └──────────────────────────────────┘  │
│                                        │
│ IBAN: IT60X0542811101000000123456      │
│ BIC: BCITITMM                          │
└────────────────────────────────────────┘
```

**Usage**:
```python
config = PDFGeneratorConfig(
    template="professional",
    logo_path="./logo.png",
    company_name="ACME S.r.l.",
    company_vat="12345678901"
)
generator = PDFGenerator(config)
```

### 3. Branded Template

**Best for**: Enterprises, agencies, high-value clients

**Features**:
- Full brand customization (colors, logo, watermark)
- Custom primary + secondary colors
- Watermark support (e.g., "BOZZA", "COPIA")
- Enhanced graphics and borders
- QR code positioning options
- Largest file size (~120KB)

**Preview**:
```
┌────────────────────────────────────────┐
│                           ╔══════════╗ │  [WATERMARK]
│ [LOGO]                    ║ FATTURA  ║ │   COPIA
│ YOUR COMPANY              ║ 001/2025 ║ │
│ Via Roma 123, Milano      ╚══════════╝ │
│                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                        │
│ DESTINATARIO                           │
│ Mario Rossi SRL                        │
│ P.IVA: 98765432109                     │
│                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                        │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│ ┃ Descrizione     Qta Prezzo Total┃   │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫   │
│ ┃ Consulenza IT     8  100.00 800 ┃   │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫   │
│ ┃              IMPONIBILE   1400.00┃   │
│ ┃              IVA 22%       308.00┃   │
│ ┃              TOTALE       1708.00┃   │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛   │
│                                        │
│ MODALITÀ DI PAGAMENTO                  │
│ Bonifico bancario                 [QR] │
│ IBAN: IT60X0542811101000000123456      │
│ Scadenza: 31/10/2025                   │
└────────────────────────────────────────┘
```

**Usage**:
```python
config = PDFGeneratorConfig(
    template="branded",
    logo_path="./logo.png",
    primary_color="#1E3A8A",      # Royal blue
    secondary_color="#60A5FA",     # Light blue
    watermark_text="COPIA",
    enable_qr_code=True
)
generator = PDFGenerator(config)
```

### Template Comparison

```python
# Generate same invoice with all 3 templates
templates = ["minimalist", "professional", "branded"]

for template in templates:
    config = PDFGeneratorConfig(template=template)
    generator = PDFGenerator(config)
    output = f"fattura_{template}.pdf"
    generator.generate(fattura, output)
    print(f"Generated: {output}")
```

---

## Configuration

### PDFGeneratorConfig

Type-safe configuration with Pydantic:

```python
from openfatture.services.pdf import PDFGeneratorConfig

config = PDFGeneratorConfig(
    # Template selection
    template="professional",  # minimalist/professional/branded

    # Company information (header)
    company_name="ACME S.r.l.",
    company_vat="12345678901",
    company_address="Via Roma 123",
    company_city="Milano, 20100 MI",
    logo_path="./logo.png",

    # Branding (for branded template)
    primary_color="#2C3E50",      # Dark blue-grey
    secondary_color="#95A5A6",    # Light grey

    # QR Code
    enable_qr_code=True,          # Enable payment QR
    qr_code_type="sepa",          # sepa or pagopa

    # PDF/A compliance
    enable_pdfa=True,             # Legal archiving

    # Watermark (for drafts)
    watermark_text="BOZZA",       # None to disable

    # Footer
    footer_text="Documento generato da OpenFatture",
)
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `template` | str | `"minimalist"` | Template name |
| `company_name` | str | `""` | Company name for header |
| `company_vat` | str | `None` | VAT number (P.IVA) |
| `company_address` | str | `None` | Street address |
| `company_city` | str | `None` | City, postal code, province |
| `logo_path` | str | `None` | Path to logo image (PNG/JPG) |
| `primary_color` | str | `"#2C3E50"` | Primary brand color (hex) |
| `secondary_color` | str | `"#95A5A6"` | Secondary brand color (hex) |
| `enable_qr_code` | bool | `False` | Enable payment QR code |
| `qr_code_type` | str | `"sepa"` | QR type (sepa/pagopa) |
| `enable_pdfa` | bool | `True` | Enable PDF/A-3 compliance |
| `watermark_text` | str | `None` | Watermark text (e.g., BOZZA) |
| `footer_text` | str | `None` | Custom footer text |

### Environment Variables

Set defaults via `.env`:

```bash
# PDF Generation
PDF_DEFAULT_TEMPLATE=professional
PDF_COMPANY_NAME=ACME S.r.l.
PDF_COMPANY_VAT=12345678901
PDF_COMPANY_ADDRESS=Via Roma 123
PDF_COMPANY_CITY=Milano, 20100 MI
PDF_LOGO_PATH=./assets/logo.png
PDF_ENABLE_QR=true
PDF_PRIMARY_COLOR=#1E3A8A
PDF_SECONDARY_COLOR=#60A5FA
```

Load in code:

```python
from openfatture.utils.config import get_settings

settings = get_settings()

config = PDFGeneratorConfig(
    template=settings.pdf_default_template,
    company_name=settings.pdf_company_name,
    company_vat=settings.pdf_company_vat,
    # ...
)
```

---

## Components

### Header Component

Draws company information at the top of the page.

```python
from openfatture.services.pdf.components import draw_header
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

canvas = Canvas("test.pdf", pagesize=A4)
y_position = 29.7 * cm  # A4 height

y_after_header = draw_header(
    canvas,
    y_position,
    company_name="ACME S.r.l.",
    company_vat="12345678901",
    company_address="Via Roma 123",
    company_city="Milano, 20100 MI",
    logo_path="./logo.png",
    primary_color="#2C3E50"
)
```

**Parameters**:
- `canvas` (Canvas): ReportLab canvas
- `y_position` (float): Starting Y coordinate
- `company_name` (str): Company name
- `company_vat` (str): VAT number
- `company_address` (str): Address
- `company_city` (str): City + postal code
- `logo_path` (str): Path to logo (optional)
- `primary_color` (str): Header color (hex)

**Returns**: New Y position after header

### Footer Component

Draws page numbers and legal notes at the bottom.

```python
from openfatture.services.pdf.components import draw_footer

draw_footer(
    canvas,
    page_number=1,
    total_pages=1,
    show_digital_signature_note=True,
    footer_text="Documento generato da OpenFatture"
)
```

**Parameters**:
- `canvas` (Canvas): ReportLab canvas
- `page_number` (int): Current page number
- `total_pages` (int): Total page count
- `show_digital_signature_note` (bool): Show P7M note
- `footer_text` (str): Custom footer text (optional)

### Invoice Table Component

Draws invoice lines with automatic column sizing.

```python
from openfatture.services.pdf.components import draw_invoice_table

righe_data = [
    {
        "descrizione": "Consulenza IT",
        "quantita": 8,
        "unita_misura": "ore",
        "prezzo_unitario": 100.00,
        "imponibile": 800.00,
        "aliquota_iva": 22,
        "iva": 176.00,
        "totale": 976.00
    },
    # ... more lines
]

y_after_table, needs_pagination = draw_invoice_table(
    canvas,
    y_position,
    righe_data,
    primary_color="#2C3E50"
)

if needs_pagination:
    print("Table requires multiple pages")
```

**Parameters**:
- `canvas` (Canvas): ReportLab canvas
- `y_position` (float): Starting Y coordinate
- `righe_data` (List[Dict]): Invoice lines
- `primary_color` (str): Header row color

**Returns**:
- `y_position` (float): New Y position
- `needs_pagination` (bool): Whether table overflows page

### QR Code Component

Draws payment QR code (SEPA EPC format).

```python
from openfatture.services.pdf.components import draw_qr_code, generate_sepa_qr_data

# Generate SEPA QR data
qr_data = generate_sepa_qr_data(
    beneficiary_name="ACME S.r.l.",
    iban="IT60X0542811101000000123456",
    amount=1708.00,
    reference="Fattura 001/2025",
    bic="BCITITMM"  # Optional
)

# Draw QR code
draw_qr_code(
    canvas,
    x_position=15.5 * cm,
    y_position=2.5 * cm,
    data=qr_data,
    size=3 * cm
)
```

**Parameters**:
- `canvas` (Canvas): ReportLab canvas
- `x_position` (float): X coordinate (left edge)
- `y_position` (float): Y coordinate (bottom edge)
- `data` (str): QR code content
- `size` (float): QR code size (cm)

---

## QR Code Integration

### SEPA EPC QR Codes

**SEPA EPC QR** codes enable instant bank transfers via mobile banking apps.

#### Format

```
BCD
002
1
SCT
BCITITMM
ACME S.r.l.
IT60X0542811101000000123456
EUR1708.00


Fattura 001/2025
```

#### Supported Banks

All Italian banks supporting SEPA Instant Credit Transfer (SCT Inst):
- Intesa Sanpaolo
- UniCredit
- Banco BPM
- BPER Banca
- And 100+ others

#### Usage

```python
config = PDFGeneratorConfig(
    enable_qr_code=True,
    qr_code_type="sepa"
)
```

### pagoPa Integration (Planned)

**pagoPa** is Italy's public administration payment system.

```python
config = PDFGeneratorConfig(
    enable_qr_code=True,
    qr_code_type="pagopa"  # Not yet implemented
)
```

---

## PDF/A Compliance

### What is PDF/A?

**PDF/A** (ISO 19005) is a subset of PDF for long-term archiving. Required by **Agenzia delle Entrate** for 10-year invoice storage.

### PDF/A-3 Features

- **Self-contained**: All fonts/images embedded
- **No external dependencies**: No JavaScript, no forms
- **Metadata**: Complete XMP metadata
- **Color profiles**: Embedded ICC profiles
- **Searchable**: Full-text search enabled

### Compliance Levels

| Level | Description | OpenFatture |
|-------|-------------|-------------|
| PDF/A-1 | Basic archiving | ❌ Not used |
| PDF/A-2 | Enhanced (layers) | ❌ Not used |
| PDF/A-3 | With attachments | ✅ **Used** |

**Why PDF/A-3?** Allows embedding the original XML invoice inside the PDF.

### Enable/Disable

```python
config = PDFGeneratorConfig(
    enable_pdfa=True  # Default: True
)
```

### Validation

Validate PDF/A compliance:

```bash
# Using VeraPDF (free validator)
verapdf fattura.pdf

# Expected output:
# PDF/A-3 compliant: Yes
```

---

## CLI Commands

### Generate PDF

```bash
# Basic generation
openfatture pdf generate <invoice_id> --output fattura.pdf

# With template
openfatture pdf generate 123 --template professional --output fattura.pdf

# With QR code
openfatture pdf generate 123 --qr-code --output fattura.pdf

# Custom logo
openfatture pdf generate 123 --logo ./logo.png --output fattura.pdf

# Watermark (for drafts)
openfatture pdf generate 123 --watermark "BOZZA" --output fattura.pdf
```

### Batch Generation

```bash
# Generate all invoices for 2025
openfatture pdf batch --year 2025 --output-dir ./pdfs/

# With specific template
openfatture pdf batch --year 2025 --template branded --output-dir ./pdfs/

# Filter by client
openfatture pdf batch --client "Mario Rossi SRL" --output-dir ./pdfs/

# Filter by date range
openfatture pdf batch --from 2025-01-01 --to 2025-12-31 --output-dir ./pdfs/
```

### Preview Template

```bash
# Preview template with sample data
openfatture pdf preview --template minimalist

# Opens PDF in default viewer
```

### List Templates

```bash
# List available templates
openfatture pdf templates

# Output:
# Available templates:
# - minimalist     (Simple, clean design)
# - professional   (With logo and branding)
# - branded        (Full customization)
```

---

## Python API

### Basic Generation

```python
from openfatture.services.pdf import PDFGenerator, PDFGeneratorConfig
from openfatture.storage.database import get_session
from openfatture.storage.database.models import Fattura

# Configure
config = PDFGeneratorConfig(template="professional")
generator = PDFGenerator(config)

# Load invoice
with get_session() as session:
    fattura = session.query(Fattura).filter_by(id=123).first()

    # Generate
    pdf_path = generator.generate(fattura)
    print(f"Generated: {pdf_path}")
```

### Factory Function

```python
from openfatture.services.pdf import create_pdf_generator

# Create generator with factory
generator = create_pdf_generator(
    template="professional",
    company_name="ACME S.r.l.",
    enable_qr_code=True
)

pdf_path = generator.generate(fattura)
```

### Batch Generation

```python
from pathlib import Path

invoices = session.query(Fattura).filter_by(anno=2025).all()
output_dir = Path("./pdfs")
output_dir.mkdir(exist_ok=True)

for fattura in invoices:
    filename = f"fattura_{fattura.numero}_{fattura.anno}.pdf"
    output_path = output_dir / filename
    generator.generate(fattura, output_path)
    print(f"✓ {filename}")
```

---

## Customization

### Custom Templates

Create custom templates by extending `BaseTemplate`:

```python
from openfatture.services.pdf.templates import BaseTemplate
from reportlab.pdfgen.canvas import Canvas

class CustomTemplate(BaseTemplate):
    """Custom template with unique design."""

    def get_primary_color(self) -> str:
        return "#1E3A8A"  # Royal blue

    def draw_invoice_info(self, canvas: Canvas, fattura_data: dict, y: float) -> float:
        """Draw invoice number and date with custom styling."""
        canvas.setFillColor(self.get_primary_color())
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(
            2 * cm,
            y,
            f"INVOICE #{fattura_data['numero']}/{fattura_data['anno']}"
        )
        return y - 1 * cm

    # Implement other required methods...
```

Register template:

```python
from openfatture.services.pdf.templates import register_template

register_template("custom", CustomTemplate)

# Use it
config = PDFGeneratorConfig(template="custom")
```

### Custom Components

Create reusable components:

```python
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm

def draw_custom_badge(canvas: Canvas, x: float, y: float, text: str):
    """Draw a custom badge on the invoice."""
    # Draw rounded rectangle
    canvas.setFillColorRGB(0.2, 0.6, 0.8)
    canvas.roundRect(x, y, 4*cm, 1*cm, 0.2*cm, fill=1)

    # Draw text
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(x + 2*cm, y + 0.3*cm, text)
```

---

## Best Practices

### 1. Template Selection

- **Freelancers**: Use `minimalist` for simplicity
- **SMBs**: Use `professional` for branding
- **Agencies**: Use `branded` for full customization
- **High-volume**: Use `minimalist` for faster generation

### 2. Logo Requirements

- **Format**: PNG (with transparency) or JPG
- **Size**: 200x60px to 400x120px (recommended)
- **DPI**: 300 DPI for print quality
- **Colors**: Match `primary_color` for consistency

### 3. QR Code Usage

- ✅ **Enable for B2C**: Makes payment easier for consumers
- ✅ **Enable for recurring clients**: Faster payment processing
- ❌ **Disable for PA**: Public administration uses different systems
- ❌ **Disable for large amounts**: Prefer manual verification

### 4. Watermarks

Use watermarks for drafts/copies:

```python
# Draft invoice
config = PDFGeneratorConfig(watermark_text="BOZZA")

# Copy for records
config = PDFGeneratorConfig(watermark_text="COPIA")

# Original (no watermark)
config = PDFGeneratorConfig(watermark_text=None)
```

### 5. Performance

```python
# Fast generation (no logo, no QR)
config = PDFGeneratorConfig(
    template="minimalist",
    logo_path=None,
    enable_qr_code=False
)

# Batch generation (reuse generator)
generator = PDFGenerator(config)
for fattura in invoices:
    generator.generate(fattura)  # ~50ms per invoice
```

---

## Troubleshooting

### Logo Not Showing

**Problem**: Logo image not appearing in PDF

**Solutions**:
1. Check file path is absolute or relative to working directory
2. Verify image format (PNG/JPG only)
3. Check file size (<2MB recommended)
4. Test with `PIL.Image.open(logo_path)` manually

```python
from PIL import Image

try:
    img = Image.open("./logo.png")
    print(f"Logo OK: {img.size}")
except Exception as e:
    print(f"Logo error: {e}")
```

### QR Code Not Scanning

**Problem**: Banking app cannot scan QR code

**Solutions**:
1. Increase QR code size (`size=4*cm` instead of `3*cm`)
2. Verify IBAN format (27 chars for Italy)
3. Check amount format (use float, not Decimal)
4. Test with online QR reader

```python
# Generate QR with larger size
draw_qr_code(canvas, x, y, qr_data, size=4*cm)
```

### Table Overflow

**Problem**: Invoice lines don't fit on one page

**Solutions**:
1. Enable pagination (TODO: currently warns only)
2. Reduce font size in table component
3. Use shorter descriptions

```python
# Temporary workaround: split long descriptions
for riga in fattura.righe:
    if len(riga.descrizione) > 50:
        riga.descrizione = riga.descrizione[:50] + "..."
```

### PDF/A Validation Fails

**Problem**: PDF/A validator reports non-compliance

**Solutions**:
1. Ensure `enable_pdfa=True` in config
2. Check all fonts are embedded
3. Verify logo uses embedded color profile
4. Use VeraPDF for detailed validation

```bash
verapdf --format text fattura.pdf
```

### Slow Generation

**Problem**: PDF generation takes >1 second per invoice

**Solutions**:
1. Use `minimalist` template (fastest)
2. Disable QR codes if not needed
3. Remove logo for batch operations
4. Reuse `PDFGenerator` instance

```python
# Slow (creates new generator each time)
for fattura in invoices:
    generator = PDFGenerator(config)  # ❌
    generator.generate(fattura)

# Fast (reuse generator)
generator = PDFGenerator(config)
for fattura in invoices:  # ✅
    generator.generate(fattura)
```

---

## Related Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started with OpenFatture
- [CLI Reference](CLI_REFERENCE.md) - Full CLI commands
- [Configuration](CONFIGURATION.md) - System configuration
- [Batch Operations](BATCH_OPERATIONS.md) - CSV import/export

---

**Last Updated**: October 10, 2025
**Module Version**: 0.2.0-rc1
**Maintainer**: OpenFatture Core Team
