"""
Email Templates Usage Examples.

Demonstrates how to use the OpenFatture email template system.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from openfatture.core.batch.processor import BatchResult
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.config import get_settings
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.sender import TemplatePECSender


def example_1_send_invoice():
    """Example 1: Send invoice to SDI with template."""
    print("\n=== Example 1: Send Invoice to SDI ===\n")

    settings = get_settings()
    sender = TemplatePECSender(settings=settings)

    # Create mock invoice (in production, load from database)
    cliente = Cliente(
        denominazione="Test Client SRL",
        partita_iva="12345678901",
    )

    fattura = Fattura(
        numero="001",
        anno=2025,
        data_emissione=date(2025, 10, 9),
        cliente=cliente,
        imponibile=Decimal("100.00"),
        iva=Decimal("22.00"),
        totale=Decimal("122.00"),
        stato=StatoFattura.DA_INVIARE,
    )

    # Create XML file (simplified - in production use XML builder)
    xml_path = Path("/tmp/IT12345678901_00001.xml")
    xml_path.write_text("<xml>test invoice</xml>")

    # Send to SDI
    success, error = sender.send_invoice_to_sdi(fattura=fattura, xml_path=xml_path, signed=False)

    if success:
        print(f"✅ Invoice {fattura.numero}/{fattura.anno} sent to SDI")
        print(f"   Status: {fattura.stato.value}")
    else:
        print(f"❌ Error: {error}")


def example_2_preview_template():
    """Example 2: Preview template without sending."""
    print("\n=== Example 2: Preview Template ===\n")

    settings = get_settings()
    renderer = TemplateRenderer(settings=settings, locale="it")

    # Create context
    from openfatture.utils.email.models import FatturaInvioContext

    cliente = Cliente(denominazione="Test Client")
    fattura = Fattura(
        numero="001",
        anno=2025,
        data_emissione=date.today(),
        cliente=cliente,
        totale=Decimal("122.00"),
    )

    context = FatturaInvioContext(
        fattura=fattura,
        cedente={
            "denominazione": settings.cedente_denominazione,
            "partita_iva": settings.cedente_partita_iva,
            "indirizzo": settings.cedente_indirizzo,
            "cap": settings.cedente_cap,
            "comune": settings.cedente_comune,
        },
        destinatario="sdi01@pec.fatturapa.it",
        is_signed=False,
        xml_filename="IT12345678901_00001.xml",
    )

    # Generate preview
    preview_path = renderer.preview(
        template_name="sdi/invio_fattura.html",
        context=context,
        output_path=Path("/tmp/email_preview.html"),
    )

    print(f"📧 Preview generated: file://{preview_path}")
    print("   Open the file in your browser to see the email template")


def example_3_batch_summary():
    """Example 3: Send batch operation summary."""
    print("\n=== Example 3: Batch Summary Email ===\n")

    settings = get_settings()
    sender = TemplatePECSender(settings=settings)

    # Create batch result
    result = BatchResult(total=100, start_time=datetime.now())
    result.succeeded = 95
    result.failed = 5
    result.errors = [
        "Row 12: Invalid VAT number",
        "Row 45: Client not found",
        "Row 67: Duplicate invoice number",
        "Row 78: Missing required field",
        "Row 89: Invalid date format",
    ]
    result.end_time = datetime.now()

    # Send summary
    if settings.notification_email:
        success, error = sender.send_batch_summary(
            result=result,
            operation_type="import",
            recipients=[settings.notification_email],
        )

        if success:
            print(f"✅ Batch summary sent to {settings.notification_email}")
            print(f"   Success rate: {result.success_rate:.1f}%")
            print(f"   Duration: {result.duration:.2f}s")
        else:
            print(f"❌ Error: {error}")
    else:
        print("⚠️  Notification email not configured")
        print("   Set NOTIFICATION_EMAIL in .env file")


def example_4_test_configuration():
    """Example 4: Test PEC configuration."""
    print("\n=== Example 4: Test PEC Configuration ===\n")

    settings = get_settings()
    sender = TemplatePECSender(settings=settings)

    # Send test email
    success, error = sender.send_test_email()

    if success:
        print("✅ PEC configuration is working!")
        print(f"   SMTP: {settings.pec_smtp_server}:{settings.pec_smtp_port}")
        print(f"   PEC: {settings.pec_address}")
        print("\n   Check your inbox for the test email.")
    else:
        print(f"❌ PEC configuration error: {error}")
        print("\n   Troubleshooting:")
        print("   1. Check PEC credentials in .env file")
        print("   2. Verify SMTP server and port")
        print("   3. Ensure firewall allows SMTP connections")


def example_5_custom_branding():
    """Example 5: Use custom branding."""
    print("\n=== Example 5: Custom Branding ===\n")

    from openfatture.utils.email.styles import EmailBranding

    settings = get_settings()

    # Create custom branding
    branding = EmailBranding(
        primary_color="#FF5722",  # Orange
        secondary_color="#212121",  # Dark gray
        success_color="#4CAF50",  # Green
        warning_color="#FFC107",  # Amber
        error_color="#F44336",  # Red
        logo_url="https://example.com/custom-logo.png",
        footer_text="© 2025 My Company - All rights reserved",
    )

    print("🎨 Custom branding configured:")
    print(f"   Primary color: {branding.primary_color}")
    print(f"   Logo URL: {branding.logo_url}")
    print(f"   Footer: {branding.footer_text}")

    # Create renderer with custom branding
    renderer = TemplateRenderer(
        settings=settings,
        locale="it",
        branding=branding,
    )

    print("\n✅ Renderer created with custom branding")
    print("   All emails will use these colors and branding")


def example_6_multi_language():
    """Example 6: Multi-language support."""
    print("\n=== Example 6: Multi-Language Support ===\n")

    settings = get_settings()

    # Italian
    renderer_it = TemplateRenderer(settings=settings, locale="it")
    print(f"🇮🇹 Italian: {renderer_it.translations['email']['common']['invoice']}")

    # English
    renderer_en = TemplateRenderer(settings=settings, locale="en")
    print(f"🇬🇧 English: {renderer_en.translations['email']['common']['invoice']}")

    print("\n✅ Multi-language support ready")
    print("   Switch locale in Settings or per-renderer")


def main():
    """Run all examples."""
    print("=" * 60)
    print("OpenFatture Email Templates - Usage Examples")
    print("=" * 60)

    try:
        example_1_send_invoice()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_preview_template()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_batch_summary()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_test_configuration()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_custom_branding()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    try:
        example_6_multi_language()
    except Exception as e:
        print(f"Example 6 failed: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
