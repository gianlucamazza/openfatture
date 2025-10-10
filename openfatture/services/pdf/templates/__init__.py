"""PDF templates for invoice generation."""

from openfatture.services.pdf.templates.base import BaseTemplate
from openfatture.services.pdf.templates.branded import BrandedTemplate
from openfatture.services.pdf.templates.minimalist import MinimalistTemplate
from openfatture.services.pdf.templates.professional import ProfessionalTemplate

__all__ = [
    "BaseTemplate",
    "MinimalistTemplate",
    "ProfessionalTemplate",
    "BrandedTemplate",
]
