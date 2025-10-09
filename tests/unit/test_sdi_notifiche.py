"""Unit tests for SDI notifications parser."""

from datetime import datetime

import pytest

from openfatture.sdi.notifiche import NotificaSDI, SDINotificationParser, TipoNotifica

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
        assert "delivered successfully" in notification.messaggio.lower()

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
        assert "rejected" in notification.messaggio.lower()

    def test_parse_mancata_consegna(self):
        """Test parsing NotificaMancataConsegna notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(MANCATA_CONSEGNA_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.MANCATA_CONSEGNA
        assert notification.identificativo_sdi == "12345680"
        assert "satura" in notification.messaggio

    def test_parse_notifica_esito_accettata(self):
        """Test parsing NotificaEsito with acceptance."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(NOTIFICA_ESITO_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.NOTIFICA_ESITO
        assert notification.esito_committente == "EC01"
        assert "accepted" in notification.messaggio.lower()

    def test_parse_notifica_esito_rifiutata(self):
        """Test parsing NotificaEsito with rejection."""
        esito_rifiutata = NOTIFICA_ESITO_XML.replace("EC01", "EC02").replace(
            "accettata", "rifiutata"
        )
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(esito_rifiutata)

        assert success is True
        assert notification.esito_committente == "EC02"
        assert "rejected" in notification.messaggio.lower()

    def test_parse_attestazione_trasmissione(self):
        """Test parsing AttestazioneTrasmissioneFattura notification."""
        parser = SDINotificationParser()
        success, error, notification = parser.parse_xml(ATTESTAZIONE_TRASMISSIONE_XML)

        assert success is True
        assert error is None
        assert notification is not None
        assert notification.tipo == TipoNotifica.ATTESTAZIONE_TRASMISSIONE
        assert notification.identificativo_sdi == "12345682"
        assert "transmitted" in notification.messaggio.lower()

    def test_parse_invalid_xml(self):
        """Test parsing invalid XML."""
        parser = SDINotificationParser()
        invalid_xml = "<?xml version='1.0'?><Invalid>content</Invalid>"

        success, error, notification = parser.parse_xml(invalid_xml)

        assert success is False
        assert "Unknown notification type" in error
        assert notification is None

    def test_parse_malformed_xml(self):
        """Test parsing malformed XML."""
        parser = SDINotificationParser()
        malformed_xml = "<?xml version='1.0'?><Unclosed>"

        success, error, notification = parser.parse_xml(malformed_xml)

        assert success is False
        assert "parsing error" in error.lower()
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
        assert notification.tipo == TipoNotifica.RICEVUTA_CONSEGNA

    def test_parse_file_not_found(self, tmp_path):
        """Test parsing non-existent file."""
        parser = SDINotificationParser()
        non_existent = tmp_path / "nonexistent.xml"

        success, error, notification = parser.parse_file(non_existent)

        assert success is False
        assert "not found" in error.lower()
        assert notification is None

    def test_notification_data_model(self):
        """Test NotificaSDI data model."""
        notification = NotificaSDI(
            tipo=TipoNotifica.RICEVUTA_CONSEGNA,
            identificativo_sdi="12345678",
            nome_file="test.xml",
            data_ricezione=datetime(2025, 10, 9, 14, 30, 0),
            messaggio="Test message",
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
