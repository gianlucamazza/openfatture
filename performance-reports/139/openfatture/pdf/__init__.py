"""PDF Generation Service for OpenFatture.

Enterprise-grade PDF generation for invoices with:
- Multiple templates (minimalist, professional, branded)
- PDF/A compliance for 10-year legal storage
- QR code support for pagoPa
- Reusable components (header, footer, table)

Example:
    >>> from openfatture.pdf import PDFGenerator
    >>>
    >>> generator = PDFGenerator(template="professional")
    >>> pdf_path = generator.generate(fattura, output_path="fattura_001.pdf")
"""

from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.pdf.templates.branded import BrandedTemplate
from openfatture.pdf.templates.minimalist import MinimalistTemplate
from openfatture.pdf.templates.professional import ProfessionalTemplate

__all__ = [
    "PDFGenerator",
    "PDFGeneratorConfig",
    "MinimalistTemplate",
    "ProfessionalTemplate",
    "BrandedTemplate",
]
