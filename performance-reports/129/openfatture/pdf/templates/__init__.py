"""PDF templates for invoice generation."""

from openfatture.pdf.templates.base import BaseTemplate
from openfatture.pdf.templates.branded import BrandedTemplate
from openfatture.pdf.templates.minimalist import MinimalistTemplate
from openfatture.pdf.templates.professional import ProfessionalTemplate

__all__ = [
    "BaseTemplate",
    "MinimalistTemplate",
    "ProfessionalTemplate",
    "BrandedTemplate",
]
