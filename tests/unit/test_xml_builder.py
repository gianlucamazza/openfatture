"""Unit tests for FatturaPA XML builder."""

from decimal import Decimal

import pytest
from lxml import etree

from openfatture.sdi.xml_builder.fatturapa import (
    FatturaPABuilder,
    generate_filename,
)
from openfatture.storage.database.models import Fattura

pytestmark = pytest.mark.unit


class TestFatturaPABuilder:
    """Tests for FatturaPA XML builder."""

    def test_build_basic_invoice(self, test_settings, sample_fattura):
        """Test building basic invoice XML."""
        builder = FatturaPABuilder(test_settings)

        xml_content = builder.build(sample_fattura)

        assert xml_content is not None
        assert 'xmlns="http://ivaservizi.agenziaentrate.gov.it' in xml_content
        assert "FatturaElettronica" in xml_content

    def test_xml_structure(self, test_settings, sample_fattura):
        """Test XML has correct structure."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))

        # Check main sections exist
        assert root.find(".//{*}FatturaElettronicaHeader") is not None
        assert root.find(".//{*}FatturaElettronicaBody") is not None

    def test_cedente_prestatore(self, test_settings, sample_fattura):
        """Test CedentePrestatore (company) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        cedente = root.find(".//{*}CedentePrestatore")

        assert cedente is not None

        # Check P.IVA
        id_fiscale = cedente.find(".//{*}IdFiscaleIVA/{*}IdCodice")
        assert id_fiscale is not None
        assert id_fiscale.text == test_settings.cedente_partita_iva

        # Check denominazione
        denominazione = cedente.find(".//{*}Denominazione")
        assert denominazione is not None
        assert denominazione.text == test_settings.cedente_denominazione

    def test_cessionario_committente(self, test_settings, sample_fattura):
        """Test CessionarioCommittente (client) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        cessionario = root.find(".//{*}CessionarioCommittente")

        assert cessionario is not None

        # Check client P.IVA
        id_codice = cessionario.find(".//{*}IdFiscaleIVA/{*}IdCodice")
        assert id_codice is not None
        assert id_codice.text == sample_fattura.cliente.partita_iva

    def test_dati_generali(self, test_settings, sample_fattura):
        """Test DatiGenerali section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        dati_gen = root.find(".//{*}DatiGenerali/{*}DatiGeneraliDocumento")

        assert dati_gen is not None

        # Check document type
        tipo_doc = dati_gen.find("{*}TipoDocumento")
        assert tipo_doc is not None
        assert tipo_doc.text == sample_fattura.tipo_documento.value

        # Check number
        numero = dati_gen.find("{*}Numero")
        assert numero is not None
        assert f"{sample_fattura.numero}/{sample_fattura.anno}" in numero.text

    def test_dettaglio_linee(self, test_settings, sample_fattura):
        """Test DettaglioLinee (line items) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        linee = root.findall(".//{*}DettaglioLinee")

        assert len(linee) == len(sample_fattura.righe)

        # Check first line
        first_line = linee[0]
        descrizione = first_line.find("{*}Descrizione")
        assert descrizione is not None
        assert descrizione.text == sample_fattura.righe[0].descrizione

    def test_dati_riepilogo(self, test_settings, sample_fattura):
        """Test DatiRiepilogo (VAT summary) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        riepilogo = root.findall(".//{*}DatiRiepilogo")

        assert len(riepilogo) > 0

        # Check first riepilogo
        first_riepilogo = riepilogo[0]
        aliquota_iva = first_riepilogo.find("{*}AliquotaIVA")
        assert aliquota_iva is not None

    def test_ritenuta_acconto(self, test_settings, sample_fattura_with_ritenuta):
        """Test withholding tax (ritenuta d'acconto) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_ritenuta)

        root = etree.fromstring(xml_content.encode("utf-8"))
        dati_ritenuta = root.find(".//{*}DatiRitenuta")

        assert dati_ritenuta is not None

        importo_ritenuta = dati_ritenuta.find("{*}ImportoRitenuta")
        assert importo_ritenuta is not None
        assert Decimal(importo_ritenuta.text) == sample_fattura_with_ritenuta.ritenuta_acconto

    def test_bollo(self, test_settings, sample_fattura_with_bollo):
        """Test stamp duty (bollo) section."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_bollo)

        root = etree.fromstring(xml_content.encode("utf-8"))
        dati_bollo = root.find(".//{*}DatiBollo")

        assert dati_bollo is not None

        bollo_virtuale = dati_bollo.find("{*}BolloVirtuale")
        assert bollo_virtuale is not None
        assert bollo_virtuale.text == "SI"

        importo_bollo = dati_bollo.find("{*}ImportoBollo")
        assert importo_bollo is not None
        assert Decimal(importo_bollo.text) == Decimal("2.00")

    def test_progressivo_invio(self, test_settings, sample_fattura):
        """Test ProgressivoInvio format."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        progressivo = root.find(".//{*}ProgressivoInvio")

        assert progressivo is not None
        expected = (
            f"{test_settings.cedente_partita_iva}_{sample_fattura.numero}_{sample_fattura.anno}"
        )
        assert progressivo.text == expected

    def test_codice_destinatario(self, test_settings, sample_fattura):
        """Test CodiceDestinatario for SDI."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        codice_dest = root.find(".//{*}CodiceDestinatario")

        assert codice_dest is not None
        assert codice_dest.text == sample_fattura.cliente.codice_destinatario

    def test_pec_destinatario(self, test_settings, sample_fattura):
        """Test PECDestinatario when CodiceDestinatario is 0000000."""
        # Modify client to use PEC
        sample_fattura.cliente.codice_destinatario = "0000000"

        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        pec_dest = root.find(".//{*}PECDestinatario")

        assert pec_dest is not None
        assert pec_dest.text == sample_fattura.cliente.pec

    def test_format_decimal(self, test_settings, sample_fattura):
        """Test decimal formatting in XML."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))

        # Find any price element
        prezzo = root.find(".//{*}PrezzoUnitario")
        assert prezzo is not None

        # Should not have trailing zeros
        assert not prezzo.text.endswith(".00")

    def test_save_to_file(self, test_settings, sample_fattura, tmp_path):
        """Test saving XML to file."""
        builder = FatturaPABuilder(test_settings)
        output_path = tmp_path / "test_invoice.xml"

        xml_content = builder.build(sample_fattura, output_path)

        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == xml_content

    def test_validate_invoice_requires_client(self, test_settings):
        """Test validation fails without client."""
        builder = FatturaPABuilder(test_settings)
        fattura = Fattura(numero="1", anno=2025)

        with pytest.raises(ValueError, match="must have a client"):
            builder.build(fattura)

    def test_validate_invoice_requires_righe(self, test_settings, sample_fattura):
        """Test validation fails without line items."""
        builder = FatturaPABuilder(test_settings)
        sample_fattura.righe.clear()

        with pytest.raises(ValueError, match="at least one line item"):
            builder.build(sample_fattura)


class TestGenerateFilename:
    """Tests for filename generation."""

    def test_standard_filename(self, test_settings, sample_fattura):
        """Test standard filename format."""
        filename = generate_filename(sample_fattura, test_settings)

        assert filename.startswith("IT")
        assert test_settings.cedente_partita_iva in filename
        assert filename.endswith(".xml")

    def test_filename_with_padding(self, test_settings, sample_fattura):
        """Test filename padding for short numbers."""
        sample_fattura.numero = "1"

        filename = generate_filename(sample_fattura, test_settings)

        # Should have 5-digit number with padding
        assert "_00001.xml" in filename
