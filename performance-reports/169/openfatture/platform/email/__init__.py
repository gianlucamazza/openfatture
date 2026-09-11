"""
Email templates and sending for OpenFatture.

Provides professional HTML + text email templates with i18n support
for SDI notifications, batch operations, and PEC communications.
"""

from openfatture.platform.email.models import (
    BatchSummaryContext,
    EmailAttachment,
    EmailMessage,
    EmailTestContext,
    FatturaInvioContext,
    NotificaSDIContext,
)
from openfatture.platform.email.renderer import TemplateRenderer
from openfatture.platform.email.sender import TemplatePECSender

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
