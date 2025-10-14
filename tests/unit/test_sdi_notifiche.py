"""Unit tests for SDI notifications parser and processor."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from openfatture.sdi.notifiche import NotificaSDI, SDINotificationParser, TipoNotifica
from openfatture.sdi.notifiche.processor import (
    NotificationProcessor,
    process_notification_directory,
)
from openfatture.storage.database.models import LogSDI, StatoFattura

pytestmark = pytest.mark.unit


# Sample notification XMLs for testing
RICEVUTA_CONSEGNA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns:RicevutaConsegna xmlns:ns="http://www.fatturapa.gov.it/sdi/messaggi/v1.0" versione="1.0">
    <IdentificativoSdI>12345678</IdentificativoSdI>
    <NomeFile>IT01234567890_00001.xml</NomeFile>
    <DataOraRicezione>2025-10-09T14:30:00</DataOraRicezione>
    <MessageId>1234567890</MessageId>
</ns:RicevutaConsegna>"""

NOTIFICA_SCARTO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns:NotificaScarto xmlns:ns="http://www.fatturapa.gov.it/sdi/messaggi/v1.0" versione="1.0">
    <IdentificativoSdI>12345679</IdentificativoSdI>
    <NomeFile>IT01234567890_00002.xml</NomeFile>
    <DataOraRicezione>2025-10-09T15:00:00</DataOraRicezione>
    <ListaErrori>
        <Errore>
            <Codice>00404</Codice>
            <Descrizione>Partita IVA inesistente</Descrizione>
        </Errore>
        <Errore>
            <Codice>00411</Codice>
            <Descrizione>Formato non valido</Descrizione>
        </Errore>
    </ListaErrori>
</ns:NotificaScarto>"""

MANCATA_CONSEGNA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns:NotificaMancataConsegna xmlns:ns="http://www.fatturapa.gov.it/sdi/messaggi/v1.0" versione="1.0">
    <IdentificativoSdI>12345680</IdentificativoSdI>
    <NomeFile>IT01234567890_00003.xml</NomeFile>
    <DataOraRicezione>2025-10-09T16:00:00</DataOraRicezione>
    <Descrizione>Casella PEC destinatario satura</Descrizione>
</ns:NotificaMancataConsegna>"""

NOTIFICA_ESITO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns:NotificaEsito xmlns:ns="http://www.fatturapa.gov.it/sdi/messaggi/v1.0" versione="1.0">
    <IdentificativoSdI>12345681</IdentificativoSdI>
    <NomeFile>IT01234567890_00004.xml</NomeFile>
    <DataOraRicezione>2025-10-09T17:00:00</DataOraRicezione>
    <Esito>EC01</Esito>
    <Descrizione>Fattura accettata</Descrizione>
</ns:NotificaEsito>"""

ATTESTAZIONE_TRASMISSIONE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns:AttestazioneTrasmissioneFattura xmlns:ns="http://www.fatturapa.gov.it/sdi/messaggi/v1.0" versione="1.0">
    <IdentificativoSdI>12345682</IdentificativoSdI>
    <NomeFile>IT01234567890_00005.xml</NomeFile>
    <DataOraRicezione>2025-10-09T18:00:00</DataOraRicezione>
</ns:AttestazioneTrasmissioneFattura>"""


class TestSDINotificationParser:
    """Tests for SDI notification parser."""

    def test_parse_ricevuta_consegna(self):
        """Test parsing RicevutaConsegna notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(RICEVUTA_CONSEGNA_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA
        assert notification.identificativo_sdi == "12345678"
        assert notification.nome_file == "IT01234567890_00001.xml"
        assert isinstance(notification.data_ricezione, datetime)
        assert notification.messaggio and "delivered successfully" in notification.messaggio.lower()

    def test_parse_notifica_scarto(self):
        """Test parsing NotificaScarto notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(NOTIFICA_SCARTO_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.NOTIFICA_SCARTO
        assert notification.identificativo_sdi == "12345679"
        assert len(notification.lista_errori) == 2
        assert "00404" in notification.lista_errori[0]
        assert "Partita IVA inesistente" in notification.lista_errori[0]
        assert notification.messaggio and "rejected" in notification.messaggio.lower()

    def test_parse_mancata_consegna(self):
        """Test parsing NotificaMancataConsegna notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(MANCATA_CONSEGNA_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.MANCATA_CONSEGNA
        assert notification.identificativo_sdi == "12345680"
        assert notification.messaggio and "satura" in notification.messaggio

    def test_parse_notifica_esito_accettata(self):
        """Test parsing NotificaEsito with acceptance."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(NOTIFICA_ESITO_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.NOTIFICA_ESITO
        assert notification.esito_committente == "EC01"
        assert notification.messaggio and "accepted" in notification.messaggio.lower()

    def test_parse_notifica_esito_rifiutata(self):
        """Test parsing NotificaEsito with rejection."""
        esito_rifiutata = NOTIFICA_ESITO_XML.replace("EC01", "EC02").replace(
            "accettata", "rifiutata"
        )
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(esito_rifiutata)

        assert success is True
        assert notification is not None
        assert notification.esito_committente == "EC02"
        assert notification.messaggio and "rejected" in notification.messaggio.lower()

    def test_parse_attestazione_trasmissione(self):
        """Test parsing AttestazioneTrasmissioneFattura notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(ATTESTAZIONE_TRASMISSIONE_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.ATTESTAZIONE_TRASMISSIONE
        assert notification.identificativo_sdi == "12345682"
        assert notification.messaggio and "transmitted" in notification.messaggio.lower()

    def test_parse_invalid_xml(self):
        """Test parsing invalid XML."""
        parser = SDINotificationParser()
        invalid_xml = "<?xml version='1.0'?><Invalid>content</Invalid>"

        success, error, notification = parser.parse_xml(invalid_xml)

        assert success is False
        assert error and "Unknown notification type" in error
        assert notification is None

    def test_parse_malformed_xml(self):
        """Test parsing malformed XML."""
        parser = SDINotificationParser()
        malformed_xml = "<?xml version='1.0'?><Unclosed>"

        success, error, notification = parser.parse_xml(malformed_xml)

        assert success is False
        assert error and "parsing error" in error.lower()
        assert notification is None

    def test_parse_file_success(self, tmp_path):
        """Test parsing from file."""
        parser = SDINotificationParser()

        # Create test XML file
        xml_file = tmp_path / "RC_test.xml"
        xml_file.write_text(RICEVUTA_CONSEGNA_XML, encoding="utf-8")

        success, error, notification = parser.parse_file(xml_file)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA

    def test_parse_file_not_found(self, tmp_path):
        """Test parsing non-existent file."""
        parser = SDINotificationParser()
        non_existent = tmp_path / "nonexistent.xml"

        success, error, notification = parser.parse_file(non_existent)

        assert success is False
        assert error and "not found" in error.lower()
        assert notification is None

    def test_notification_data_model(self):
        """Test NotificaSDI data model."""
        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Test message",
            esito_committente=None,
        )

        assert notification.tipo == "RC"  # Enum value
        assert notification.identificativo_sdi == "12345678"
        assert notification.lista_errori == []  # Default empty list

    def test_notification_with_errors(self):
        """Test NotificaSDI with error list."""
        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_SCARTO,
            identificativo_sdi="12345679",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 15, 0, 0),
            messaggio="Rejected",
            lista_errori=["Error 1", "Error 2"],
            esito_committente=None,
        )

        assert len(notification.lista_errori) == 2
        assert notification.tipo == "NS"

    def test_datetime_parsing_iso_format(self):
        """Test datetime parsing with ISO format."""
        parser = SDINotificationParser()
        dt = parser._parse_datetime("2025-10-09T14:30:00")

        assert dt.year == 2025
        assert dt.month == 10
        assert dt.day == 9
        assert dt.hour == 14
        assert dt.minute == 30

    def test_datetime_parsing_with_timezone(self):
        """Test datetime parsing with timezone."""
        parser = SDINotificationParser()
        dt = parser._parse_datetime("2025-10-09T14:30:00Z")

        assert dt.year == 2025

    def test_datetime_parsing_fallback(self):
        """Test datetime parsing fallback for invalid format."""
        parser = SDINotificationParser()
        dt = parser._parse_datetime("invalid-date")

        # Should fallback to current datetime
        assert isinstance(dt, datetime)

    def test_get_text_with_namespace(self):
        """Test _get_text helper with namespace."""
        parser = SDINotificationParser()
        import xml.etree.ElementTree as ET

        xml = """<root xmlns:ns="http://test"><ns:element>value</ns:element></root>"""
        root = ET.fromstring(xml)

        # With namespace, need to use the full path with namespace
        text = parser._get_text(root, ".//{http://test}element")
        assert text == "value"

    def test_get_text_empty_element(self):
        """Test _get_text with empty element."""
        parser = SDINotificationParser()
        import xml.etree.ElementTree as ET

        xml = """<root><empty/></root>"""
        root = ET.fromstring(xml)

        text = parser._get_text(root, ".//empty")
        assert text == ""  # Should return empty string

    def test_all_notification_types_enum(self):
        """Test that all notification types are covered."""
        assert TipoNotifica.RICEVUTA_CONSEGNA == "RC"
        assert TipoNotifica.NOTIFICA_SCARTO == "NS"
        assert TipoNotifica.MANCATA_CONSEGNA == "MC"
        assert TipoNotifica.NOTIFICA_ESITO == "NE"
        assert TipoNotifica.ATTESTAZIONE_TRASMISSIONE == "AT"


class TestNotificationProcessor:
    """Tests for SDI notification processor."""

    def test_processor_initialization(self, db_session):
        """Test processor initialization."""
        processor = NotificationProcessor(db_session)

        assert processor.db == db_session
        assert processor.parser is not None
        assert processor.email_sender is None

    def test_processor_with_email_sender(self, db_session):
        """Test processor initialization with email sender."""
        mock_sender = MagicMock()
        processor = NotificationProcessor(db_session, mock_sender)

        assert processor.email_sender == mock_sender

    def test_process_file_success(self, db_session, sample_fattura, tmp_path):
        """Test successful file processing."""
        # Create a test notification XML
        xml_content = RICEVUTA_CONSEGNA_XML.replace(
            "IT01234567890_00001.xml", f"IT01234567890_{sample_fattura.numero}.xml"
        )
        xml_file = tmp_path / "test_notification.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        processor = NotificationProcessor(db_session)
        success, error, notification = processor.process_file(xml_file)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA

        # Check that invoice status was updated
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.CONSEGNATA

        # Check that log was created
        log = db_session.query(LogSDI).filter_by(fattura_id=sample_fattura.id).first()
        assert log is not None
        assert log.tipo_notifica == "RC"
        assert log.fattura_id == sample_fattura.id

    def test_process_file_parsing_failure(self, db_session, tmp_path):
        """Test processing file with parsing failure."""
        # Create invalid XML file
        xml_file = tmp_path / "invalid.xml"
        xml_file.write_text("<?xml version='1.0'?><Invalid>content</Invalid>", encoding="utf-8")

        processor = NotificationProcessor(db_session)
        success, error, notification = processor.process_file(xml_file)

        assert success is False
        assert error is not None
        assert "Unknown notification type" in error
        assert notification is None

    def test_process_file_not_found(self, db_session, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "nonexistent.xml"

        processor = NotificationProcessor(db_session)
        success, error, notification = processor.process_file(non_existent)

        assert success is False
        assert error is not None
        assert "not found" in error.lower()
        assert notification is None

    def test_process_notification_invoice_not_found(self, db_session):
        """Test processing notification when invoice is not found."""
        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="99999999",
            nome_file="IT01234567890_999.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered successfully",
            esito_committente=None,
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is False
        assert error is not None
        assert "Invoice not found" in error
        assert notification_result == notification

    def test_process_notification_status_update_consegnata(self, db_session, sample_fattura):
        """Test status update to CONSEGNATA."""
        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered successfully",
            esito_committente=None,
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is True
        assert error is None
        assert notification_result == notification

        # Check status update
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.CONSEGNATA

    def test_process_notification_status_update_scartata(self, db_session, sample_fattura):
        """Test status update to SCARTATA."""
        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_SCARTO,
            identificativo_sdi="12345679",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 15, 0, 0),
            messaggio="Rejected by SDI",
            lista_errori=["Error 1", "Error 2"],
            esito_committente=None,
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is True
        assert error is None

        # Check status update
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.SCARTATA

        # Check notes were added
        assert sample_fattura.note is not None
        assert "SDI Notification" in sample_fattura.note
        assert "Error 1" in sample_fattura.note
        assert "Error 2" in sample_fattura.note

    def test_process_notification_status_update_errore(self, db_session, sample_fattura):
        """Test status update to ERRORE."""
        notification = NotificaSDI(
            tipo=TipoNotifica.MANCATA_CONSEGNA,
            identificativo_sdi="12345680",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 16, 0, 0),
            messaggio="Delivery failed",
            esito_committente=None,
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is True
        assert error is None

        # Check status update
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.ERRORE

    def test_process_notification_esito_accettata(self, db_session, sample_fattura):
        """Test NotificaEsito with acceptance."""
        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_ESITO,
            identificativo_sdi="12345681",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 17, 0, 0),
            messaggio="Accepted by recipient",
            esito_committente="EC01",
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is True
        assert error is None

        # Check status update
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.ACCETTATA

    def test_process_notification_esito_rifiutata(self, db_session, sample_fattura):
        """Test NotificaEsito with rejection."""
        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_ESITO,
            identificativo_sdi="12345682",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 18, 0, 0),
            messaggio="Rejected by recipient",
            esito_committente="EC02",
        )

        processor = NotificationProcessor(db_session)
        success, error, notification_result = processor.process_notification(notification)

        assert success is True
        assert error is None

        # Check status update
        db_session.refresh(sample_fattura)
        assert sample_fattura.stato == StatoFattura.RIFIUTATA

    def test_process_notification_with_email_sender(self, db_session, sample_fattura):
        """Test notification processing with email sender."""
        mock_sender = MagicMock()
        processor = NotificationProcessor(db_session, mock_sender)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered successfully",
            esito_committente=None,
        )

        success, error, _ = processor.process_notification(notification)

        assert success is True
        # Check that email notification was sent
        mock_sender.notify_consegna.assert_called_once()

    def test_process_notification_email_error_handling(self, db_session, sample_fattura):
        """Test that email errors don't fail notification processing."""
        mock_sender = MagicMock()
        mock_sender.notify_consegna.side_effect = Exception("Email error")

        processor = NotificationProcessor(db_session, mock_sender)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered successfully",
            esito_committente=None,
        )

        success, error, _ = processor.process_notification(notification)

        # Processing should still succeed despite email error
        assert success is True
        assert error is None

        # Email was attempted
        mock_sender.notify_consegna.assert_called_once()

    def test_find_invoice_by_filename(self, db_session, sample_fattura):
        """Test invoice finding by filename pattern."""
        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file=f"IT01234567890_{sample_fattura.numero}.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Test",
            esito_committente=None,
        )

        found_invoice = processor._find_invoice(notification)
        assert found_invoice == sample_fattura

    def test_find_invoice_not_found(self, db_session):
        """Test invoice finding when no match exists."""
        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="99999999",
            nome_file="IT01234567890_999.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Test",
            esito_committente=None,
        )

        found_invoice = processor._find_invoice(notification)
        assert found_invoice is None

    def test_determine_new_status_mapping(self, db_session):
        """Test status determination from notification types."""
        processor = NotificationProcessor(db_session)

        # Test each notification type
        test_cases = [
            (TipoNotifica.ATTESTAZIONE_TRASMISSIONE, StatoFattura.INVIATA),
            (TipoNotifica.RICEVUTA_CONSEGNA, StatoFattura.CONSEGNATA),
            (TipoNotifica.NOTIFICA_SCARTO, StatoFattura.SCARTATA),
            (TipoNotifica.MANCATA_CONSEGNA, StatoFattura.ERRORE),
        ]

        for tipo_notifica, expected_status in test_cases:
            notification = NotificaSDI(
                tipo=tipo_notifica,
                identificativo_sdi="12345678",
                nome_file="test.xml",
                data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
                messaggio="Test",
                esito_committente=None,
            )

            new_status = processor._determine_new_status(notification)
            assert new_status == expected_status

    def test_determine_new_status_esito_accettata(self, db_session):
        """Test status determination for accepted esito."""
        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_ESITO,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Accepted",
            esito_committente="EC01",
        )

        new_status = processor._determine_new_status(notification)
        assert new_status == StatoFattura.ACCETTATA

    def test_determine_new_status_esito_rifiutata(self, db_session):
        """Test status determination for rejected esito."""
        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_ESITO,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Rejected",
            esito_committente="EC02",
        )

        new_status = processor._determine_new_status(notification)
        assert new_status == StatoFattura.RIFIUTATA

    def test_add_notification_note(self, db_session, sample_fattura):
        """Test adding notification details to invoice notes."""
        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.NOTIFICA_SCARTO,
            identificativo_sdi="12345679",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 15, 0, 0),
            messaggio="Rejected with errors",
            lista_errori=["Error 1", "Error 2"],
            esito_committente=None,
        )

        processor._add_notification_note(sample_fattura, notification)

        assert sample_fattura.note is not None
        assert "SDI Notification (NS): Rejected with errors" in sample_fattura.note
        assert "Error 1" in sample_fattura.note
        assert "Error 2" in sample_fattura.note

    def test_add_notification_note_append(self, db_session, sample_fattura):
        """Test appending notification notes to existing notes."""
        sample_fattura.note = "Existing note"

        processor = NotificationProcessor(db_session)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered",
            esito_committente=None,
        )

        processor._add_notification_note(sample_fattura, notification)

        assert sample_fattura.note.startswith("Existing note")
        assert "SDI Notification (RC): Delivered" in sample_fattura.note

    def test_send_email_notification_without_sender(self, db_session, sample_fattura):
        """Test that email notification is skipped when no sender configured."""
        processor = NotificationProcessor(db_session)  # No email sender

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered",
            esito_committente=None,
        )

        # This should not raise an error
        processor._send_email_notification(sample_fattura, notification)

    def test_send_email_notification_with_sender(self, db_session, sample_fattura):
        """Test email notification sending."""
        mock_sender = MagicMock()
        processor = NotificationProcessor(db_session, mock_sender)

        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Delivered",
            esito_committente=None,
        )

        processor._send_email_notification(sample_fattura, notification)

        mock_sender.notify_consegna.assert_called_once_with(sample_fattura, notification)

    def test_send_email_notification_all_types(self, db_session, sample_fattura):
        """Test email notification for all notification types."""
        mock_sender = MagicMock()
        processor = NotificationProcessor(db_session, mock_sender)

        test_cases = [
            (TipoNotifica.ATTESTAZIONE_TRASMISSIONE, "notify_attestazione_trasmissione"),
            (TipoNotifica.RICEVUTA_CONSEGNA, "notify_consegna"),
            (TipoNotifica.NOTIFICA_SCARTO, "notify_scarto"),
            (TipoNotifica.MANCATA_CONSEGNA, "notify_mancata_consegna"),
            (TipoNotifica.NOTIFICA_ESITO, "notify_esito"),
        ]

        for tipo_notifica, method_name in test_cases:
            mock_sender.reset_mock()

            notification = NotificaSDI(
                tipo=tipo_notifica,
                identificativo_sdi="12345678",
                nome_file="test.xml",
                data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
                messaggio="Test",
                esito_committente="EC01" if tipo_notifica == TipoNotifica.NOTIFICA_ESITO else None,
            )

            processor._send_email_notification(sample_fattura, notification)

            method = getattr(mock_sender, method_name)
            method.assert_called_once()

            if tipo_notifica == TipoNotifica.NOTIFICA_ESITO:
                # Check that accepted parameter was passed correctly
                call_args = method.call_args
                assert call_args[0][2] is True  # accepted=True for EC01


def test_process_notification_directory(db_session, tmp_path):
    """Test processing multiple notifications in a directory."""
    # Create test notification files
    xml_files = [
        ("RC_test.xml", RICEVUTA_CONSEGNA_XML),
        ("NS_test.xml", NOTIFICA_SCARTO_XML),
    ]

    for filename, content in xml_files:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")

    processed, errors, error_messages = process_notification_directory(tmp_path, db_session)

    # Since no matching invoices exist, all should be errors
    assert processed == 0
    assert errors == 2
    assert len(error_messages) == 2
    assert all("Invoice not found" in msg for msg in error_messages)
