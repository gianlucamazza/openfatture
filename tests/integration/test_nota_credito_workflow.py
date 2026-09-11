"""Integration tests for nota di credito (credit note) workflow.

Tests the complete TD04 flow:
- Application service create_nota_credito_from_fattura
- FatturaPA XML generation with DatiFattureCollegate
- Model linkage (fattura_collegata_id/numero/data)
- Full and partial refund scenarios
- No mocks or stubs - real models and XML builder
"""

from datetime import date
from decimal import Decimal

import pytest
from lxml import etree

from openfatture.billing.application.nota_credito_ops import (
    create_nota_credito_from_fattura,
)
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


@pytest.fixture
def cliente_with_invoice(runtime_session):
    """Create a client with a complete source invoice."""
    db = runtime_session
    # Create cliente
    cliente = Cliente(
        denominazione="Test Client SRL",
        partita_iva="12345678901",
        codice_fiscale="12345678901",
        indirizzo="Via Test 123",
        cap="00100",
        comune="Roma",
        provincia="RM",
        nazione="IT",
    )
    db.add(cliente)
    db.flush()

    # Create source fattura TD01
    fattura = Fattura(
        numero="001",
        anno=2025,
        data_emissione=date(2025, 1, 15),
        tipo_documento=TipoDocumento.TD01,
        cliente_id=cliente.id,
        stato=StatoFattura.BOZZA,
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
    )
    db.add(fattura)
    db.flush()

    # Add line items
    riga1 = RigaFattura(
        fattura_id=fattura.id,
        numero_riga=1,
        descrizione="Consulting services",
        quantita=Decimal("10"),
        prezzo_unitario=Decimal("80.00"),
        unita_misura="ore",
        aliquota_iva=Decimal("22.00"),
        imponibile=Decimal("800.00"),
        iva=Decimal("176.00"),
        totale=Decimal("976.00"),
    )
    riga2 = RigaFattura(
        fattura_id=fattura.id,
        numero_riga=2,
        descrizione="Development work",
        quantita=Decimal("2"),
        prezzo_unitario=Decimal("100.00"),
        unita_misura="ore",
        aliquota_iva=Decimal("22.00"),
        imponibile=Decimal("200.00"),
        iva=Decimal("44.00"),
        totale=Decimal("244.00"),
    )
    db.add(riga1)
    db.add(riga2)
    db.commit()
    db.refresh(fattura)
    db.refresh(cliente)

    return {"cliente": cliente, "fattura": fattura}


def test_create_nota_credito_full_refund(runtime_session, cliente_with_invoice, runtime_db):
    """Test creating a full refund nota di credito."""
    db = runtime_session
    source_fattura = cliente_with_invoice["fattura"]

    # Create nota di credito with full refund
    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        note="Full refund - customer request",
        full_refund=True,
    )

    # Assert success
    assert "error" not in result
    assert result["success"] is True
    assert result["tipo_documento"] == "TD04"
    assert result["totale"] == float(source_fattura.totale)

    # Load nota di credito from DB
    nota_credito = db.query(Fattura).filter(Fattura.id == result["nota_credito_id"]).first()
    assert nota_credito is not None
    assert nota_credito.tipo_documento == TipoDocumento.TD04
    assert nota_credito.stato == StatoFattura.BOZZA

    # Verify linkage fields
    assert nota_credito.fattura_collegata_id == source_fattura.id
    assert nota_credito.fattura_collegata_numero == f"{source_fattura.numero}/{source_fattura.anno}"
    assert nota_credito.fattura_collegata_data == source_fattura.data_emissione

    # Verify amounts match source
    assert nota_credito.imponibile == source_fattura.imponibile
    assert nota_credito.iva == source_fattura.iva
    assert nota_credito.totale == source_fattura.totale

    # Verify same client
    assert nota_credito.cliente_id == source_fattura.cliente_id

    # Verify line items copied
    assert len(nota_credito.righe) == len(source_fattura.righe)
    for nc_riga, src_riga in zip(nota_credito.righe, source_fattura.righe, strict=False):
        assert nc_riga.numero_riga == src_riga.numero_riga
        assert nc_riga.descrizione == src_riga.descrizione
        assert nc_riga.quantita == src_riga.quantita
        assert nc_riga.prezzo_unitario == src_riga.prezzo_unitario
        assert nc_riga.aliquota_iva == src_riga.aliquota_iva
        assert nc_riga.imponibile == src_riga.imponibile


def test_create_nota_credito_partial_refund(runtime_session, cliente_with_invoice, runtime_db):
    """Test creating a partial refund nota di credito."""
    db = runtime_session
    source_fattura = cliente_with_invoice["fattura"]

    # Create partial nota di credito - refund only first line, partial quantity
    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        note="Partial refund - 5 hours of consulting",
        full_refund=False,
        line_items=[
            {"numero_riga": 1, "quantita": 5.0}  # Half of the original 10 hours
        ],
    )

    # Assert success
    assert "error" not in result
    assert result["success"] is True
    assert result["tipo_documento"] == "TD04"

    # Load nota di credito from DB
    nota_credito = db.query(Fattura).filter(Fattura.id == result["nota_credito_id"]).first()
    assert nota_credito is not None

    # Verify linkage
    assert nota_credito.fattura_collegata_id == source_fattura.id

    # Verify only one line item
    assert len(nota_credito.righe) == 1
    riga = nota_credito.righe[0]
    assert riga.numero_riga == 1
    assert riga.quantita == Decimal("5.0")
    assert riga.prezzo_unitario == Decimal("80.00")

    # Verify amounts are half of first line
    expected_imponibile = Decimal("400.00")  # 5 * 80
    expected_iva = Decimal("88.00")  # 400 * 0.22
    expected_totale = Decimal("488.00")

    assert riga.imponibile == expected_imponibile
    assert nota_credito.imponibile == expected_imponibile
    assert nota_credito.iva == expected_iva
    assert nota_credito.totale == expected_totale


def test_create_nota_credito_invalid_source(runtime_db):
    """Test creating nota di credito with invalid source invoice."""
    result = create_nota_credito_from_fattura(
        fattura_id=99999,  # Non-existent
        note="Test",
    )

    assert "error" in result
    assert "not found" in result["error"].lower()


def test_create_nota_credito_partial_invalid_line(runtime_db, cliente_with_invoice):
    """Test partial refund with invalid line number."""
    source_fattura = cliente_with_invoice["fattura"]

    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        full_refund=False,
        line_items=[
            {"numero_riga": 999, "quantita": 1.0}  # Non-existent line
        ],
    )

    assert "error" in result
    assert "not found" in result["error"].lower()


def test_create_nota_credito_partial_invalid_quantity(runtime_db, cliente_with_invoice):
    """Test partial refund with invalid quantity."""
    source_fattura = cliente_with_invoice["fattura"]

    # Try to refund more than original quantity
    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        full_refund=False,
        line_items=[
            {"numero_riga": 1, "quantita": 20.0}  # Original was 10
        ],
    )

    assert "error" in result
    assert "invalid quantity" in result["error"].lower()


def test_fatturapa_xml_with_dati_fatture_collegate(runtime_session, cliente_with_invoice, test_settings, runtime_db):
    """Test FatturaPA XML generation includes DatiFattureCollegate for TD04."""
    db = runtime_session
    settings = test_settings
    source_fattura = cliente_with_invoice["fattura"]

    # Create nota di credito
    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        note="Test XML generation",
        full_refund=True,
    )
    assert "error" not in result

    # Load nota di credito
    nota_credito = db.query(Fattura).filter(Fattura.id == result["nota_credito_id"]).first()
    assert nota_credito is not None

    # Generate FatturaPA XML
    builder = FatturaPABuilder(settings)
    xml_string = builder.build(nota_credito)

    # Parse XML
    root = etree.fromstring(xml_string.encode("utf-8"))
    ns = {"f": "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"}

    # Verify TipoDocumento is TD04
    tipo_doc = root.xpath("//f:TipoDocumento", namespaces=ns)
    assert len(tipo_doc) == 1
    assert tipo_doc[0].text == "TD04"

    # Verify DatiFattureCollegate exists
    dati_coll = root.xpath("//f:DatiFattureCollegate", namespaces=ns)
    assert len(dati_coll) == 1, "DatiFattureCollegate must be present for TD04"

    # Verify IdDocumento
    id_doc = root.xpath("//f:DatiFattureCollegate/f:IdDocumento", namespaces=ns)
    assert len(id_doc) == 1
    assert id_doc[0].text == f"{source_fattura.numero}/{source_fattura.anno}"

    # Verify Data
    data = root.xpath("//f:DatiFattureCollegate/f:Data", namespaces=ns)
    assert len(data) == 1
    assert data[0].text == source_fattura.data_emissione.isoformat()


def test_fatturapa_xml_without_linkage_no_dati_fatture_collegate(runtime_db, cliente_with_invoice, test_settings):
    """Test FatturaPA XML generation does NOT include DatiFattureCollegate for regular TD01."""
    settings = test_settings
    fattura = cliente_with_invoice["fattura"]

    # Generate FatturaPA XML for source invoice (TD01)
    builder = FatturaPABuilder(settings)
    xml_string = builder.build(fattura)

    # Parse XML
    root = etree.fromstring(xml_string.encode("utf-8"))
    ns = {"f": "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"}

    # Verify TipoDocumento is TD01
    tipo_doc = root.xpath("//f:TipoDocumento", namespaces=ns)
    assert len(tipo_doc) == 1
    assert tipo_doc[0].text == "TD01"

    # Verify DatiFattureCollegate does NOT exist
    dati_coll = root.xpath("//f:DatiFattureCollegate", namespaces=ns)
    assert len(dati_coll) == 0, "DatiFattureCollegate must not be present for TD01 without linkage"


def test_nota_credito_amounts_with_positive_values(runtime_session, cliente_with_invoice, runtime_db):
    """Test nota di credito uses positive amounts (TD04 standard practice), not negative."""
    db = runtime_session
    source_fattura = cliente_with_invoice["fattura"]

    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        full_refund=True,
    )
    assert "error" not in result

    nota_credito = db.query(Fattura).filter(Fattura.id == result["nota_credito_id"]).first()

    # All amounts must be positive (TD04 standard)
    assert nota_credito.imponibile > 0
    assert nota_credito.iva > 0
    assert nota_credito.totale > 0

    for riga in nota_credito.righe:
        assert riga.quantita > 0
        assert riga.prezzo_unitario > 0
        assert riga.imponibile > 0
        assert riga.totale > 0


def test_nota_credito_preserves_natura_codes(runtime_session, cliente_with_invoice, runtime_db):
    """Test nota di credito preserves natura codes from source invoice."""
    db = runtime_session
    source_fattura = cliente_with_invoice["fattura"]

    # Add a line with natura code (zero-rated VAT)
    riga_natura = RigaFattura(
        fattura_id=source_fattura.id,
        numero_riga=3,
        descrizione="EU export",
        quantita=Decimal("1"),
        prezzo_unitario=Decimal("100.00"),
        unita_misura="pz",
        aliquota_iva=Decimal("0.00"),
        natura="N3.1",  # Non imponibili - esportazioni
        imponibile=Decimal("100.00"),
        iva=Decimal("0.00"),
        totale=Decimal("100.00"),
    )
    db.add(riga_natura)
    db.commit()
    db.refresh(source_fattura)

    # Create nota di credito
    result = create_nota_credito_from_fattura(
        fattura_id=source_fattura.id,
        full_refund=True,
    )
    assert "error" not in result

    nota_credito = db.query(Fattura).filter(Fattura.id == result["nota_credito_id"]).first()

    # Find the copied line with natura
    riga_with_natura = [r for r in nota_credito.righe if r.numero_riga == 3]
    assert len(riga_with_natura) == 1
    assert riga_with_natura[0].natura == "N3.1"
    assert riga_with_natura[0].aliquota_iva == Decimal("0.00")
