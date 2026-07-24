"""
Email templates and sending for OpenFatture.

Provides professional HTML + text email templates with i18n support
for SDI notifications, batch operations, and PEC communications.
"""

from openfatture.utils.email.models import (
    BatchSummaryContext,
    EmailAttachment,
    EmailMessage,
    EmailTestContext,
    FatturaInvioContext,
    NotificaSDIContext,
)
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.sender import TemplatePECSender

__all__ = [
    "EmailAttachment",
    "EmailMessage",
    "FatturaInvioContext",
    "NotificaSDIContext",
    "BatchSummaryContext",
    "EmailTestContext",
    "TemplateRenderer",
    "TemplatePECSender",
]
