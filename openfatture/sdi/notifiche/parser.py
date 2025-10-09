"""
SDI notification parser for FatturaPA.

Parses XML notifications received from Sistema di Interscambio (SDI):
- RicevutaConsegna (RC) - Delivery receipt
- NotificaScarto (NS) - Rejection notification
- NotificaMancataConsegna (MC) - Failed delivery
- NotificaEsito (NE) - Outcome notification
- AttestazioneTrasmissioneFattura (AT) - Transmission attestation
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field


class TipoNotifica(str, Enum):
    """SDI notification types."""

    RICEVUTA_CONSEGNA = "RC"  # Delivery receipt - invoice delivered to recipient
    NOTIFICA_SCARTO = "NS"  # Rejection - invoice rejected by SDI
    MANCATA_CONSEGNA = "MC"  # Failed delivery - recipient system unavailable
    NOTIFICA_ESITO = "NE"  # Outcome - recipient acceptance/rejection
    ATTESTAZIONE_TRASMISSIONE = "AT"  # Transmission attestation - sent to SDI


class NotificaSDI(BaseModel):
    """
    Parsed SDI notification data.

    Represents a notification received from SDI about invoice processing.
    """

    tipo: TipoNotifica = Field(..., description="Notification type")
    identificativo_sdi: str = Field(..., description="SDI identifier (unique per invoice)")
    nome_file: str = Field(..., description="Original invoice filename")
    data_ricezione: datetime = Field(..., description="Notification reception date")
    messaggio: str | None = Field(None, description="Notification message/description")
    lista_errori: list[str] = Field(default_factory=list, description="List of errors (for NS)")
    esito_committente: str | None = Field(
        None, description="Recipient outcome: EC01=accepted, EC02=rejected"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SDINotificationParser:
    """
    Parser for SDI XML notifications.

    Parses different types of notifications from Sistema di Interscambio.

    Usage:
        parser = SDINotificationParser()
        notification = parser.parse_file(Path("RC_IT01234567890_00001.xml"))
    """

    # XML namespaces used by SDI
    NAMESPACES = {
        "ns": "http://www.fatturapa.gov.it/sdi/messaggi/v1.0",
        "types": "http://www.fatturapa.gov.it/sdi/types/v1.0",
    }

    def parse_file(self, xml_path: Path) -> tuple[bool, str | None, NotificaSDI | None]:
        """
        Parse SDI notification XML file.

        Args:
            xml_path: Path to notification XML file

        Returns:
            Tuple[bool, Optional[str], Optional[NotificaSDI]]: (success, error, notification)
        """
        if not xml_path.exists():
            return False, f"File not found: {xml_path}", None

        try:
            xml_content = xml_path.read_text(encoding="utf-8")
            return self.parse_xml(xml_content)
        except Exception as e:
            return False, f"Failed to read file: {e}", None

    def parse_xml(self, xml_content: str) -> tuple[bool, str | None, NotificaSDI | None]:
        """
        Parse SDI notification XML content.

        Args:
            xml_content: XML string content

        Returns:
            Tuple[bool, Optional[str], Optional[NotificaSDI]]: (success, error, notification)
        """
        try:
            root = ET.fromstring(xml_content)

            # Determine notification type from root tag
            root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

            if root_tag == "RicevutaConsegna":
                return self._parse_ricevuta_consegna(root)
            elif root_tag == "NotificaScarto":
                return self._parse_notifica_scarto(root)
            elif root_tag == "NotificaMancataConsegna":
                return self._parse_mancata_consegna(root)
            elif root_tag == "NotificaEsito":
                return self._parse_notifica_esito(root)
            elif root_tag == "AttestazioneTrasmissioneFattura":
                return self._parse_attestazione_trasmissione(root)
            else:
                return False, f"Unknown notification type: {root_tag}", None

        except ET.ParseError as e:
            return False, f"XML parsing error: {e}", None
        except Exception as e:
            return False, f"Parsing failed: {e}", None

    def _parse_ricevuta_consegna(
        self, root: ET.Element
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """Parse RicevutaConsegna (RC) notification."""
        try:
            identificativo_sdi = self._get_text(root, ".//IdentificativoSdI")
            nome_file = self._get_text(root, ".//NomeFile")
            data_ricezione_str = self._get_text(root, ".//DataOraRicezione")
            data_ricezione = self._parse_datetime(data_ricezione_str)

            messaggio = self._get_text(root, ".//MessageId")

            notification = NotificaSDI(
                tipo=TipoNotifica.RICEVUTA_CONSEGNA,
                identificativo_sdi=identificativo_sdi,
                nome_file=nome_file,
                data_ricezione=data_ricezione,
                messaggio=f"Invoice delivered successfully. MessageId: {messaggio}",
            )

            return True, None, notification

        except Exception as e:
            return False, f"Failed to parse RicevutaConsegna: {e}", None

    def _parse_notifica_scarto(
        self, root: ET.Element
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """Parse NotificaScarto (NS) notification."""
        try:
            identificativo_sdi = self._get_text(root, ".//IdentificativoSdI")
            nome_file = self._get_text(root, ".//NomeFile")
            data_ricezione_str = self._get_text(root, ".//DataOraRicezione")
            data_ricezione = self._parse_datetime(data_ricezione_str)

            # Extract error list
            lista_errori = []
            for errore in root.findall(".//Errore", self.NAMESPACES):
                codice = self._get_text(errore, ".//Codice")
                descrizione = self._get_text(errore, ".//Descrizione")
                lista_errori.append(f"{codice}: {descrizione}")

            messaggio = f"Invoice rejected by SDI. {len(lista_errori)} error(s) found."

            notification = NotificaSDI(
                tipo=TipoNotifica.NOTIFICA_SCARTO,
                identificativo_sdi=identificativo_sdi,
                nome_file=nome_file,
                data_ricezione=data_ricezione,
                messaggio=messaggio,
                lista_errori=lista_errori,
            )

            return True, None, notification

        except Exception as e:
            return False, f"Failed to parse NotificaScarto: {e}", None

    def _parse_mancata_consegna(
        self, root: ET.Element
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """Parse NotificaMancataConsegna (MC) notification."""
        try:
            identificativo_sdi = self._get_text(root, ".//IdentificativoSdI")
            nome_file = self._get_text(root, ".//NomeFile")
            data_ricezione_str = self._get_text(root, ".//DataOraRicezione")
            data_ricezione = self._parse_datetime(data_ricezione_str)

            descrizione = self._get_text(root, ".//Descrizione")
            messaggio = f"Failed delivery: {descrizione}"

            notification = NotificaSDI(
                tipo=TipoNotifica.MANCATA_CONSEGNA,
                identificativo_sdi=identificativo_sdi,
                nome_file=nome_file,
                data_ricezione=data_ricezione,
                messaggio=messaggio,
            )

            return True, None, notification

        except Exception as e:
            return False, f"Failed to parse NotificaMancataConsegna: {e}", None

    def _parse_notifica_esito(
        self, root: ET.Element
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """Parse NotificaEsito (NE) notification."""
        try:
            identificativo_sdi = self._get_text(root, ".//IdentificativoSdI")
            nome_file = self._get_text(root, ".//NomeFile")
            data_ricezione_str = self._get_text(root, ".//DataOraRicezione")
            data_ricezione = self._parse_datetime(data_ricezione_str)

            esito = self._get_text(root, ".//Esito")
            descrizione = self._get_text(root, ".//Descrizione")

            esito_text = "accepted" if esito == "EC01" else "rejected" if esito == "EC02" else esito
            messaggio = f"Recipient outcome: {esito_text}. {descrizione}"

            notification = NotificaSDI(
                tipo=TipoNotifica.NOTIFICA_ESITO,
                identificativo_sdi=identificativo_sdi,
                nome_file=nome_file,
                data_ricezione=data_ricezione,
                messaggio=messaggio,
                esito_committente=esito,
            )

            return True, None, notification

        except Exception as e:
            return False, f"Failed to parse NotificaEsito: {e}", None

    def _parse_attestazione_trasmissione(
        self, root: ET.Element
    ) -> tuple[bool, str | None, NotificaSDI | None]:
        """Parse AttestazioneTrasmissioneFattura (AT) notification."""
        try:
            identificativo_sdi = self._get_text(root, ".//IdentificativoSdI")
            nome_file = self._get_text(root, ".//NomeFile")
            data_ricezione_str = self._get_text(root, ".//DataOraRicezione")
            data_ricezione = self._parse_datetime(data_ricezione_str)

            messaggio = "Invoice successfully transmitted to SDI"

            notification = NotificaSDI(
                tipo=TipoNotifica.ATTESTAZIONE_TRASMISSIONE,
                identificativo_sdi=identificativo_sdi,
                nome_file=nome_file,
                data_ricezione=data_ricezione,
                messaggio=messaggio,
            )

            return True, None, notification

        except Exception as e:
            return False, f"Failed to parse AttestazioneTrasmissioneFattura: {e}", None

    def _get_text(self, element: ET.Element, path: str) -> str:
        """
        Extract text from XML element.

        Args:
            element: XML element
            path: XPath to text element

        Returns:
            Text content or empty string if not found
        """
        found = element.find(path, self.NAMESPACES)
        if found is not None and found.text:
            return found.text.strip()
        # Try without namespace
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return ""

    def _parse_datetime(self, dt_string: str) -> datetime:
        """
        Parse SDI datetime format.

        SDI uses format: YYYY-MM-DDTHH:MM:SS

        Args:
            dt_string: Datetime string

        Returns:
            Parsed datetime
        """
        if not dt_string:
            return datetime.now()

        try:
            # Try with microseconds
            return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try standard format
                return datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                # Fallback
                return datetime.now()
