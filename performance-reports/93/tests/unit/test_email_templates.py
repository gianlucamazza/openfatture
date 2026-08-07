"""Unit tests for email templates."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.core.batch.processor import BatchResult
from openfatture.sdi.notifiche.parser import NotificaSDI, TipoNotifica
from openfatture.storage.database.models import Cliente, Fattura, StatoFattura
from openfatture.utils.config import Settings
from openfatture.utils.email.models import (
    BatchSummaryContext,
    EmailAttachment,
    EmailMessage,
    FatturaInvioContext,
    InvoiceSummary,
    NotificaSDIContext,
)
from openfatture.utils.email.renderer import TemplateRenderer
from openfatture.utils.email.sender import TemplatePECSender
from openfatture.utils.email.styles import EmailBranding, EmailStyles

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.app_name = "OpenFatture Test"
    settings.cedente_denominazione = "Test Company SRL"
    settings.cedente_partita_iva = "12345678901"
    settings.cedente_indirizzo = "Via Test 123"
    settings.cedente_cap = "00100"
    settings.cedente_comune = "Roma"
    settings.cedente_provincia = "RM"
    settings.cedente_email = "test@test.it"
    settings.cedente_telefono = "+39 06 1234567"
    settings.pec_address = "test@pec.it"
    settings.pec_password = "password"
    settings.pec_smtp_server = "smtp.pec.it"
    settings.pec_smtp_port = 465
    settings.sdi_pec_address = "sdi01@pec.fatturapa.it"
    settings.email_primary_color = "#1976D2"
    settings.email_secondary_color = "#424242"
    settings.email_logo_url = None
    settings.email_footer_text = None
    settings.notification_email = "notify@test.it"
    settings.notification_enabled = True
    settings.locale = "it"
    return settings


@pytest.fixture
def mock_fattura(mock_cliente):
    """Create mock invoice."""
    fattura = Mock(spec=Fattura)
    fattura.id = 1
    fattura.numero = "001"
    fattura.anno = 2025
    fattura.data_emissione = date(2025, 10, 9)
    fattura.cliente_id = 1
    fattura.cliente = mock_cliente
    fattura.imponibile = Decimal("100.00")
    fattura.iva = Decimal("22.00")
    fattura.totale = Decimal("122.00")
    fattura.note = ""
    fattura.stato = StatoFattura.BOZZA
    fattura.numero_sdi = None
    return fattura


@pytest.fixture
def mock_cliente():
    """Create mock client."""
    cliente = Mock(spec=Cliente)
    cliente.id = 1
    cliente.denominazione = "Test Client SRL"
    cliente.partita_iva = "98765432109"
    cliente.codice_fiscale = None
    cliente.indirizzo = "Via Cliente 456"
    cliente.cap = "00200"
    cliente.comune = "Milano"
    cliente.provincia = "MI"
    cliente.pec = "cliente@pec.it"
    return cliente


@pytest.fixture
def mock_notification():
    """Create mock SDI notification."""
    notification = Mock(spec=NotificaSDI)
    notification.tipo = TipoNotifica.RICEVUTA_CONSEGNA
    notification.identificativo_sdi = "12345678"
    notification.nome_file = "IT12345678901_00001.xml"
    notification.data_ricezione = datetime(2025, 10, 9, 14, 30, 0)
    notification.messaggio = "Invoice delivered successfully."
    notification.lista_errori = []
    notification.esito_committente = None
    return notification


class TestEmailBranding:
    """Tests for EmailBranding."""

    def test_default_branding(self):
        """Test default branding configuration."""
        branding = EmailBranding()

        assert branding.primary_color == "#1976D2"
        assert branding.secondary_color == "#424242"
        assert branding.success_color == "#4CAF50"
        assert branding.error_color == "#F44336"
        assert branding.logo_url is None

    def test_custom_branding(self):
        """Test custom branding."""
        branding = EmailBranding(
            primary_color="#FF0000",
            logo_url="https://example.com/logo.png",
        )

        assert branding.primary_color == "#FF0000"
        assert branding.logo_url == "https://example.com/logo.png"


class TestEmailStyles:
    """Tests for EmailStyles."""

    def test_get_base_css(self):
        """Test base CSS generation."""
        branding = EmailBranding()
        css = EmailStyles.get_base_css(branding)

        assert "font-family" in css
        assert branding.primary_color in css
        assert ".email-container" in css
        assert ".button" in css

    def test_get_table_css(self):
        """Test table CSS generation."""
        branding = EmailBranding()
        css = EmailStyles.get_table_css(branding)

        assert "table.data-table" in css
        assert "border-collapse" in css

    def test_get_complete_css(self):
        """Test complete CSS includes all parts."""
        branding = EmailBranding()
        css = EmailStyles.get_complete_css(branding)

        assert ".email-container" in css
        assert "table.data-table" in css
        assert ".badge" in css


class TestPydanticModels:
    """Tests for Pydantic context models."""

    def test_email_attachment(self):
        """Test EmailAttachment model."""
        attachment = EmailAttachment(
            filename="test.xml",
            content=b"<xml>test</xml>",
            mime_type="application/xml",
        )

        assert attachment.filename == "test.xml"
        assert attachment.content == b"<xml>test</xml>"
        assert attachment.mime_type == "application/xml"

    def test_email_attachment_validation(self):
        """Test EmailAttachment validation."""
        with pytest.raises(ValueError):
            EmailAttachment(filename="", content=b"test")

    def test_email_message(self):
        """Test EmailMessage model."""
        message = EmailMessage(
            subject="Test Subject",
            html_body="<p>Test</p>",
            text_body="Test",
            recipients=["test@example.com"],
        )

        assert message.subject == "Test Subject"
        assert len(message.recipients) == 1
        assert len(message.attachments) == 0

    def test_email_message_validation(self):
        """Test EmailMessage validation."""
        with pytest.raises(ValueError):
            EmailMessage(
                subject="Test",
                html_body="<p>Test</p>",
                text_body="Test",
                recipients=[],  # Empty recipients
            )

    def test_fattura_invio_context(self, mock_fattura):
        """Test FatturaInvioContext model."""
        context = FatturaInvioContext(
            fattura=mock_fattura,
            cedente={"denominazione": "Test Company", "partita_iva": "12345678901"},
            destinatario="sdi@pec.it",
            is_signed=False,
            xml_filename="IT12345678901_00001.xml",
        )

        assert context.fattura == mock_fattura
        assert context.is_signed is False

    def test_notifica_sdi_context(self, mock_fattura, mock_cliente, mock_notification):
        """Test NotificaSDIContext model."""
        context = NotificaSDIContext(
            notification=mock_notification,
            fattura=mock_fattura,
            cliente=mock_cliente,
            tipo_notifica=TipoNotifica.RICEVUTA_CONSEGNA,
        )

        assert context.notification == mock_notification
        assert context.tipo_notifica == TipoNotifica.RICEVUTA_CONSEGNA

    def test_batch_summary_context(self):
        """Test BatchSummaryContext model."""
        result = BatchResult(total=10, start_time=datetime.now())
        result.succeeded = 8
        result.failed = 2
        result.end_time = datetime.now()  # Set end time

        context = BatchSummaryContext(
            result=result,
            operation_type="import",
        )

        assert context.result == result
        assert context.operation_type == "import"
        assert "s" in context.duration_formatted  # Contains seconds
        assert "%" in context.success_rate_formatted

    def test_batch_summary_context_validation(self):
        """Test BatchSummaryContext validation."""
        result = BatchResult(total=10)

        with pytest.raises(ValueError):
            BatchSummaryContext(
                result=result,
                operation_type="invalid",  # Not in allowed list
            )

    def test_invoice_summary_from_fattura(self, mock_fattura):
        """Test InvoiceSummary.from_fattura()."""
        summary = InvoiceSummary.from_fattura(mock_fattura)

        assert summary.numero == "001"
        assert summary.anno == 2025
        assert "€" in summary.totale
        assert "122,00" in summary.totale  # Italian format


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    def test_init(self, mock_settings):
        """Test renderer initialization."""
        renderer = TemplateRenderer(settings=mock_settings, locale="it")

        assert renderer.locale == "it"
        assert renderer.settings == mock_settings
        assert renderer.env is not None

    def test_load_translations_it(self, mock_settings):
        """Test loading Italian translations."""
        renderer = TemplateRenderer(settings=mock_settings, locale="it")

        assert "email" in renderer.translations
        assert "sdi" in renderer.translations["email"]

    def test_load_translations_fallback(self, mock_settings):
        """Test fallback to Italian for unknown locale."""
        renderer = TemplateRenderer(settings=mock_settings, locale="zz")

        # Should fallback to IT
        assert "email" in renderer.translations

    def test_currency_filter(self, mock_settings):
        """Test currency filter."""
        renderer = TemplateRenderer(settings=mock_settings)

        # Test filter is registered
        assert "currency" in renderer.env.filters

    def test_date_it_filter(self, mock_settings):
        """Test Italian date filter."""
        renderer = TemplateRenderer(settings=mock_settings)

        assert "date_it" in renderer.env.filters

    def test_render_html_base_template(self, mock_settings):
        """Test rendering base HTML template."""
        renderer = TemplateRenderer(settings=mock_settings)

        # Should have access to global context
        assert renderer.env.globals["app_name"] == "OpenFatture Test"
        assert renderer.env.globals["cedente_denominazione"] == "Test Company SRL"

    def test_render_both(self, mock_settings, mock_fattura):
        """Test rendering both HTML and text."""
        renderer = TemplateRenderer(settings=mock_settings)

        context = FatturaInvioContext(
            fattura=mock_fattura,
            cedente={
                "denominazione": "Test Company",
                "partita_iva": "12345678901",
                "indirizzo": "Via Test 123",
                "cap": "00100",
                "comune": "Roma",
            },
            destinatario="sdi@pec.it",
            is_signed=False,
            xml_filename="test.xml",
        )

        html, text = renderer.render_both("sdi/invio_fattura", context)

        # HTML should contain HTML tags
        assert "<html" in html.lower()
        assert "<body" in html.lower()
        assert mock_fattura.numero in html

        # Text should not contain HTML tags
        assert "<html" not in text.lower()
        assert mock_fattura.numero in text


class TestTemplatePECSender:
    """Tests for TemplatePECSender."""

    def test_init(self, mock_settings):
        """Test sender initialization."""
        sender = TemplatePECSender(settings=mock_settings)

        assert sender.settings == mock_settings
        assert sender.renderer is not None
        assert sender.rate_limiter is not None

    @patch("smtplib.SMTP_SSL")
    def test_send_test_email(self, mock_smtp, mock_settings):
        """Test sending test email."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.send_test_email()

        assert success is True
        assert error is None
        assert mock_server.login.called
        assert mock_server.send_message.called

    @patch("smtplib.SMTP_SSL")
    def test_send_invoice_to_sdi(self, mock_smtp, mock_settings, mock_fattura, tmp_path):
        """Test sending invoice to SDI."""
        # Create test XML file
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("<xml>test</xml>")

        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.send_invoice_to_sdi(mock_fattura, xml_path)

        assert success is True
        assert error is None
        assert mock_fattura.stato == StatoFattura.INVIATA
        assert mock_server.send_message.called

    @patch("smtplib.SMTP_SSL")
    def test_send_batch_summary(self, mock_smtp, mock_settings):
        """Test sending batch summary email."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = BatchResult(total=10, start_time=datetime.now())
        result.succeeded = 8
        result.failed = 2
        result.end_time = datetime.now()

        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.send_batch_summary(result, "import", ["test@example.com"])

        if not success:
            print(f"Error: {error}")

        assert success is True, f"Failed with error: {error}"
        assert error is None
        assert mock_server.send_message.called

    def test_send_invoice_missing_xml(self, mock_settings, mock_fattura):
        """Test error handling for missing XML file."""
        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.send_invoice_to_sdi(mock_fattura, Path("/nonexistent.xml"))

        assert success is False
        assert error is not None
        assert "not found" in error.lower()

    @patch("smtplib.SMTP_SSL")
    def test_notify_consegna(self, mock_smtp, mock_settings, mock_fattura, mock_notification):
        """Test delivery notification email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.notify_consegna(mock_fattura, mock_notification)

        assert success is True
        assert error is None

    @patch("smtplib.SMTP_SSL")
    def test_notify_scarto(self, mock_smtp, mock_settings, mock_fattura):
        """Test rejection notification email."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_SCARTO,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime.now(),
            messaggio="Invoice rejected",
            lista_errori=["Error 1", "Error 2"],
        )

        sender = TemplatePECSender(settings=mock_settings)
        success, error = sender.notify_scarto(mock_fattura, notification)

        assert success is True
        assert error is None

    @patch("smtplib.SMTP_SSL")
    def test_retry_on_transient_error(self, mock_smtp, mock_settings, mock_fattura, tmp_path):
        """Test retry logic for transient errors."""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("<xml>test</xml>")

        # First attempt fails, second succeeds
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = [
            ConnectionError("Temporary error"),
            None,  # Success on retry
        ]

        sender = TemplatePECSender(settings=mock_settings, max_retries=2)

        with patch("time.sleep"):  # Don't actually sleep in tests
            success, error = sender.send_invoice_to_sdi(mock_fattura, xml_path)

        # Should succeed after retry
        assert mock_server.send_message.call_count == 2


class TestEmailIntegration:
    """Integration tests for email system."""

    @patch("smtplib.SMTP_SSL")
    def test_full_notification_flow(
        self, mock_smtp, mock_settings, mock_fattura, mock_notification
    ):
        """Test complete notification flow with email."""
        from openfatture.sdi.notifiche.processor import NotificationProcessor

        # Setup mocks
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        mock_db = Mock()
        mock_db.query.return_value.all.return_value = [mock_fattura]

        # Create sender and processor
        sender = TemplatePECSender(settings=mock_settings)
        processor = NotificationProcessor(db_session=mock_db, email_sender=sender)

        # Process notification
        success, error, result = processor.process_notification(mock_notification)

        if not success:
            print(f"Error: {error}")

        assert success is True, f"Failed with error: {error}"
        assert error is None
        # Email should have been sent
        assert mock_server.send_message.called

    def test_all_templates_exist(self, mock_settings):
        """Test that all required templates exist."""
        from pathlib import Path

        templates_dir = (
            Path(__file__).parent.parent.parent / "openfatture" / "utils" / "email" / "templates"
        )

        required_templates = [
            "base.html",
            "base.txt",
            "sdi/invio_fattura.html",
            "sdi/invio_fattura.txt",
            "sdi/notifica_consegna.html",
            "sdi/notifica_consegna.txt",
            "sdi/notifica_scarto.html",
            "sdi/notifica_scarto.txt",
            "sdi/notifica_attestazione.html",
            "sdi/notifica_attestazione.txt",
            "sdi/notifica_mancata_consegna.html",
            "sdi/notifica_mancata_consegna.txt",
            "sdi/notifica_esito_accettata.html",
            "sdi/notifica_esito_accettata.txt",
            "sdi/notifica_esito_rifiutata.html",
            "sdi/notifica_esito_rifiutata.txt",
            "batch/riepilogo_batch.html",
            "batch/riepilogo_batch.txt",
            "test/test_email.html",
            "test/test_email.txt",
        ]

        for template in required_templates:
            template_path = templates_dir / template
            assert template_path.exists(), f"Template missing: {template}"

    def test_i18n_files_exist(self):
        """Test that i18n files exist."""
        from pathlib import Path

        i18n_dir = Path(__file__).parent.parent.parent / "openfatture" / "utils" / "email" / "i18n"

        assert (i18n_dir / "it.json").exists()
        assert (i18n_dir / "en.json").exists()

    def test_template_filters_error_handling(self, mock_settings):
        """Test template filters handle invalid inputs gracefully."""
        renderer = TemplateRenderer(settings=mock_settings)

        # Test currency filter with invalid input
        assert renderer.env.filters["currency"]("invalid") == "€invalid"
        assert renderer.env.filters["currency"](None) == "€None"

        # Test percentage filter with invalid input
        assert renderer.env.filters["percentage"]("invalid") == "invalid%"

        # Test duration filter with invalid input
        assert renderer.env.filters["duration"]("invalid") == "invalid"

    def test_template_filters_functionality(self, mock_settings):
        """Test template filters work correctly."""
        renderer = TemplateRenderer(settings=mock_settings)

        # Test currency filter
        assert renderer.env.filters["currency"](1234.56) == "€1.234,56"
        assert renderer.env.filters["currency"](100) == "€100,00"

        # Test percentage filter
        assert renderer.env.filters["percentage"](85.5) == "85.5%"

        # Test duration filter
        assert renderer.env.filters["duration"](30) == "30.0s"
        assert renderer.env.filters["duration"](120) == "2.0m"
        assert renderer.env.filters["duration"](7200) == "2.0h"

    def test_render_html_template_not_found(self, mock_settings):
        """Test render_html with non-existent template."""
        renderer = TemplateRenderer(settings=mock_settings)

        with pytest.raises(FileNotFoundError, match="Template not found"):
            renderer.render_html("nonexistent/template.html", {})

    def test_render_text_template_not_found(self, mock_settings):
        """Test render_text with non-existent template."""
        renderer = TemplateRenderer(settings=mock_settings)

        with pytest.raises(FileNotFoundError, match="Template not found"):
            renderer.render_text("nonexistent/template.txt", {})

    def test_preview_template(self, mock_settings, tmp_path):
        """Test template preview generation."""
        renderer = TemplateRenderer(settings=mock_settings)

        output_path = tmp_path / "preview.html"
        result_path = renderer.preview("test/test_email.html", {}, output_path)

        assert result_path == output_path
        assert output_path.exists()
        content = output_path.read_text()
        assert "<html" in content.lower()

    def test_get_renderer_factory(self):
        """Test get_renderer factory function."""
        from openfatture.utils.email.renderer import get_renderer

        renderer = get_renderer(locale="en")
        assert renderer.locale == "en"
        assert renderer.settings is not None
