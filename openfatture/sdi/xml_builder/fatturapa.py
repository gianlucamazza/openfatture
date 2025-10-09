"""FatturaPA XML v1.9 builder according to official specifications."""

from decimal import Decimal
from pathlib import Path

from lxml import etree

from openfatture.storage.database.models import Fattura
from openfatture.utils.config import Settings


class FatturaPABuilder:
    """
    Builder for FatturaPA XML v1.9 (valid from April 1, 2025).

    Supports:
    - TD01 (Fattura ordinaria)
    - TD06 (Parcella)
    - All regime fiscale types
    - Ritenuta d'acconto
    - Bollo virtuale
    """

    # XML namespace
    NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"

    def __init__(self, settings: Settings):
        """
        Initialize builder with application settings.

        Args:
            settings: Application configuration
        """
        self.settings = settings

    def build(self, fattura: Fattura, output_path: Path | None = None) -> str:
        """
        Build FatturaPA XML from invoice model.

        Args:
            fattura: Invoice database model
            output_path: Optional path to save XML file

        Returns:
            str: XML content as string

        Raises:
            ValueError: If invoice data is invalid
        """
        self._validate_invoice(fattura)

        # Create root element
        root = etree.Element(
            f"{{{self.NS}}}FatturaElettronica",
            versione="FPR12",
            nsmap={None: self.NS},
        )

        # Build sections
        self._build_header(root, fattura)
        self._build_body(root, fattura)

        # Convert to string
        xml_string = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        ).decode("utf-8")

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(xml_string, encoding="utf-8")

        return xml_string

    def _validate_invoice(self, fattura: Fattura) -> None:
        """Validate invoice has required data."""
        if not fattura.cliente:
            raise ValueError("Invoice must have a client")

        if not self.settings.cedente_partita_iva:
            raise ValueError("Cedente Partita IVA not configured")

        if not fattura.righe:
            raise ValueError("Invoice must have at least one line item")

    def _build_header(self, root: etree.Element, fattura: Fattura) -> None:
        """Build FatturaElettronicaHeader section."""
        header = etree.SubElement(root, "FatturaElettronicaHeader")

        # DatiTrasmissione
        self._build_dati_trasmissione(header, fattura)

        # CedentePrestatore (Your company)
        self._build_cedente_prestatore(header)

        # CessionarioCommittente (Client)
        self._build_cessionario_committente(header, fattura)

    def _build_dati_trasmissione(self, header: etree.Element, fattura: Fattura) -> None:
        """Build DatiTrasmissione section."""
        dati_tr = etree.SubElement(header, "DatiTrasmissione")

        # IdTrasmittente
        id_trasf = etree.SubElement(dati_tr, "IdTrasmittente")
        etree.SubElement(id_trasf, "IdPaese").text = "IT"
        etree.SubElement(id_trasf, "IdCodice").text = self.settings.cedente_partita_iva

        # ProgressivoInvio (unique transmission ID)
        # Format: PIVA_NUMERO_ANNO (e.g., 12345678901_00001_2025)
        progressivo = f"{self.settings.cedente_partita_iva}_{fattura.numero}_{fattura.anno}"
        etree.SubElement(dati_tr, "ProgressivoInvio").text = progressivo

        # FormatoTrasmissione
        etree.SubElement(dati_tr, "FormatoTrasmissione").text = "FPR12"

        # CodiceDestinatario (7 chars, or 0000000 for PEC)
        codice_dest = fattura.cliente.codice_destinatario or "0000000"
        etree.SubElement(dati_tr, "CodiceDestinatario").text = codice_dest

        # PEC (if CodiceDestinatario is 0000000)
        if codice_dest == "0000000" and fattura.cliente.pec:
            etree.SubElement(dati_tr, "PECDestinatario").text = fattura.cliente.pec

    def _build_cedente_prestatore(self, header: etree.Element) -> None:
        """Build CedentePrestatore section (your company)."""
        cedente = etree.SubElement(header, "CedentePrestatore")

        # DatiAnagrafici
        dati_anag = etree.SubElement(cedente, "DatiAnagrafici")

        # IdFiscaleIVA
        id_fiscale = etree.SubElement(dati_anag, "IdFiscaleIVA")
        etree.SubElement(id_fiscale, "IdPaese").text = "IT"
        etree.SubElement(id_fiscale, "IdCodice").text = self.settings.cedente_partita_iva

        # CodiceFiscale (if different from P.IVA)
        if self.settings.cedente_codice_fiscale != self.settings.cedente_partita_iva:
            etree.SubElement(dati_anag, "CodiceFiscale").text = self.settings.cedente_codice_fiscale

        # Anagrafica
        anagrafica = etree.SubElement(dati_anag, "Anagrafica")
        etree.SubElement(anagrafica, "Denominazione").text = self.settings.cedente_denominazione

        # RegimeFiscale
        etree.SubElement(dati_anag, "RegimeFiscale").text = self.settings.cedente_regime_fiscale

        # Sede
        sede = etree.SubElement(cedente, "Sede")
        etree.SubElement(sede, "Indirizzo").text = self.settings.cedente_indirizzo
        etree.SubElement(sede, "CAP").text = self.settings.cedente_cap
        etree.SubElement(sede, "Comune").text = self.settings.cedente_comune
        etree.SubElement(sede, "Provincia").text = self.settings.cedente_provincia
        etree.SubElement(sede, "Nazione").text = self.settings.cedente_nazione

        # Contatti (optional)
        if self.settings.cedente_telefono or self.settings.cedente_email:
            contatti = etree.SubElement(cedente, "Contatti")
            if self.settings.cedente_telefono:
                etree.SubElement(contatti, "Telefono").text = self.settings.cedente_telefono
            if self.settings.cedente_email:
                etree.SubElement(contatti, "Email").text = self.settings.cedente_email

    def _build_cessionario_committente(self, header: etree.Element, fattura: Fattura) -> None:
        """Build CessionarioCommittente section (client)."""
        cliente = fattura.cliente
        cessionario = etree.SubElement(header, "CessionarioCommittente")

        # DatiAnagrafici
        dati_anag = etree.SubElement(cessionario, "DatiAnagrafici")

        # IdFiscaleIVA (if P.IVA exists)
        if cliente.partita_iva:
            id_fiscale = etree.SubElement(dati_anag, "IdFiscaleIVA")
            etree.SubElement(id_fiscale, "IdPaese").text = cliente.nazione
            etree.SubElement(id_fiscale, "IdCodice").text = cliente.partita_iva

        # CodiceFiscale (required if no P.IVA)
        if cliente.codice_fiscale:
            etree.SubElement(dati_anag, "CodiceFiscale").text = cliente.codice_fiscale

        # Anagrafica
        anagrafica = etree.SubElement(dati_anag, "Anagrafica")
        etree.SubElement(anagrafica, "Denominazione").text = cliente.denominazione

        # Sede
        sede = etree.SubElement(cessionario, "Sede")
        etree.SubElement(sede, "Indirizzo").text = cliente.indirizzo or "N/D"
        etree.SubElement(sede, "CAP").text = cliente.cap or "00000"
        etree.SubElement(sede, "Comune").text = cliente.comune or "N/D"
        etree.SubElement(sede, "Provincia").text = cliente.provincia or "EE"
        etree.SubElement(sede, "Nazione").text = cliente.nazione

    def _build_body(self, root: etree.Element, fattura: Fattura) -> None:
        """Build FatturaElettronicaBody section."""
        body = etree.SubElement(root, "FatturaElettronicaBody")

        # DatiGenerali
        self._build_dati_generali(body, fattura)

        # DatiBeniServizi
        self._build_dati_beni_servizi(body, fattura)

        # DatiPagamento (optional but recommended)
        self._build_dati_pagamento(body, fattura)

    def _build_dati_generali(self, body: etree.Element, fattura: Fattura) -> None:
        """Build DatiGenerali section."""
        dati_gen = etree.SubElement(body, "DatiGenerali")

        # DatiGeneraliDocumento
        dati_doc = etree.SubElement(dati_gen, "DatiGeneraliDocumento")

        etree.SubElement(dati_doc, "TipoDocumento").text = fattura.tipo_documento.value
        etree.SubElement(dati_doc, "Divisa").text = "EUR"
        etree.SubElement(dati_doc, "Data").text = fattura.data_emissione.isoformat()
        etree.SubElement(dati_doc, "Numero").text = f"{fattura.numero}/{fattura.anno}"

        # Ritenuta (withholding tax)
        if fattura.ritenuta_acconto and fattura.ritenuta_acconto > 0:
            dati_rit = etree.SubElement(dati_doc, "DatiRitenuta")
            etree.SubElement(dati_rit, "TipoRitenuta").text = "RT01"  # Ritenuta persone fisiche
            etree.SubElement(dati_rit, "ImportoRitenuta").text = self._format_decimal(
                fattura.ritenuta_acconto
            )
            etree.SubElement(dati_rit, "AliquotaRitenuta").text = self._format_decimal(
                fattura.aliquota_ritenuta or Decimal("0")
            )
            etree.SubElement(dati_rit, "CausalePagamento").text = "A"  # Prestazioni lavoro autonomo

        # Bollo (stamp duty)
        if fattura.importo_bollo and fattura.importo_bollo > 0:
            dati_bollo = etree.SubElement(dati_doc, "DatiBollo")
            etree.SubElement(dati_bollo, "BolloVirtuale").text = "SI"
            etree.SubElement(dati_bollo, "ImportoBollo").text = self._format_decimal(
                fattura.importo_bollo
            )

    def _build_dati_beni_servizi(self, body: etree.Element, fattura: Fattura) -> None:
        """Build DatiBeniServizi section (line items)."""
        dati_beni = etree.SubElement(body, "DatiBeniServizi")

        # DettaglioLinee (line items)
        for riga in fattura.righe:
            dettaglio = etree.SubElement(dati_beni, "DettaglioLinee")

            etree.SubElement(dettaglio, "NumeroLinea").text = str(riga.numero_riga)
            etree.SubElement(dettaglio, "Descrizione").text = riga.descrizione

            etree.SubElement(dettaglio, "Quantita").text = self._format_decimal(riga.quantita)
            etree.SubElement(dettaglio, "UnitaMisura").text = riga.unita_misura
            etree.SubElement(dettaglio, "PrezzoUnitario").text = self._format_decimal(
                riga.prezzo_unitario
            )
            etree.SubElement(dettaglio, "PrezzoTotale").text = self._format_decimal(riga.imponibile)
            etree.SubElement(dettaglio, "AliquotaIVA").text = self._format_decimal(
                riga.aliquota_iva
            )

        # DatiRiepilogo (VAT summary by rate)
        from collections import defaultdict

        riepilogo_by_aliquota = defaultdict(lambda: Decimal("0"))

        for riga in fattura.righe:
            riepilogo_by_aliquota[riga.aliquota_iva] += riga.imponibile

        for aliquota, imponibile in riepilogo_by_aliquota.items():
            riepilogo = etree.SubElement(dati_beni, "DatiRiepilogo")

            etree.SubElement(riepilogo, "AliquotaIVA").text = self._format_decimal(aliquota)
            etree.SubElement(riepilogo, "ImponibileImporto").text = self._format_decimal(imponibile)

            iva_importo = imponibile * aliquota / Decimal("100")
            etree.SubElement(riepilogo, "Imposta").text = self._format_decimal(iva_importo)

            # Natura (for zero-rated VAT)
            if aliquota == Decimal("0"):
                etree.SubElement(riepilogo, "Natura").text = "N2.2"  # Non soggette ad IVA

            # EsigibilitaIVA
            etree.SubElement(riepilogo, "EsigibilitaIVA").text = "I"  # Immediata

    def _build_dati_pagamento(self, body: etree.Element, fattura: Fattura) -> None:
        """Build DatiPagamento section."""
        dati_pag = etree.SubElement(body, "DatiPagamento")

        # CondizioniPagamento
        etree.SubElement(dati_pag, "CondizioniPagamento").text = "TP02"  # Pagamento completo

        # DettaglioPagamento
        dettaglio_pag = etree.SubElement(dati_pag, "DettaglioPagamento")

        # Modalità pagamento (MP05 = Bonifico)
        etree.SubElement(dettaglio_pag, "ModalitaPagamento").text = "MP05"

        # Data scadenza (default: 30 giorni)
        from datetime import timedelta

        data_scadenza = fattura.data_emissione + timedelta(days=30)
        etree.SubElement(dettaglio_pag, "DataScadenzaPagamento").text = data_scadenza.isoformat()

        # Importo (total - ritenuta)
        importo_pagamento = fattura.totale
        if fattura.ritenuta_acconto:
            importo_pagamento -= fattura.ritenuta_acconto

        etree.SubElement(dettaglio_pag, "ImportoPagamento").text = self._format_decimal(
            importo_pagamento
        )

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        """
        Format Decimal for XML (remove trailing zeros).

        Args:
            value: Decimal value

        Returns:
            str: Formatted string
        """
        # Format with 2 decimals, then remove trailing zeros
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        return formatted if formatted else "0"


def generate_filename(fattura: Fattura, settings: Settings) -> str:
    """
    Generate standard FatturaPA filename.

    Format: ITPPPPPPPPPPPP_NNNNN.xml
    - IT: country code
    - PPPPPPPPPPPP: VAT number (11 digits, padded)
    - NNNNN: progressive number (5 digits, padded)

    Args:
        fattura: Invoice model
        settings: Application settings

    Returns:
        str: Filename
    """
    piva = settings.cedente_partita_iva.zfill(11)
    numero = str(fattura.numero).zfill(5)

    return f"IT{piva}_{numero}.xml"
