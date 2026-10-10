"""XSS autoescape coverage for payment reminder HTML templates."""

from pathlib import Path

import pytest

from openfatture.payment.application.notifications.notifier import EmailNotifier, SMTPConfig


@pytest.mark.asyncio
async def test_html_template_escapes_untrusted_fields(tmp_path: Path) -> None:
    """Invoice/client values interpolated into HTML must be escaped."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "reminder_email.html").write_text(
        "<p>Invoice {{ invoice_number }}</p>",
        encoding="utf-8",
    )

    notifier = EmailNotifier(
        SMTPConfig(host="localhost", from_email="billing@example.com"),
        template_dir=template_dir,
    )

    html = await notifier._render_template(
        "reminder_email.html",
        {"invoice_number": '<script>alert("xss")</script>'},
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.asyncio
async def test_text_template_is_not_html_escaped(tmp_path: Path) -> None:
    """Plain-text reminders should keep literal characters such as &."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "reminder_email.txt").write_text(
        "Company: {{ company_name }}",
        encoding="utf-8",
    )

    notifier = EmailNotifier(
        SMTPConfig(host="localhost", from_email="billing@example.com"),
        template_dir=template_dir,
    )

    text = await notifier._render_template(
        "reminder_email.txt",
        {"company_name": "Rossi & Figli"},
    )

    assert text == "Company: Rossi & Figli"
