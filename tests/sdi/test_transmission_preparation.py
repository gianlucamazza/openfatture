"""Only validated XML that matches the current invoice is transmitted."""

from pathlib import Path

from openfatture.billing.fatture.service import InvoiceService
from openfatture.platform.config import get_settings
from openfatture.sdi.application.invoice_sdi_ops import _prepare_transmission
from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import Fattura, RigaFattura


def _service() -> InvoiceService:
    return InvoiceService(get_settings())


def test_unsigned_send_regenerates_and_validates_stale_xml(runtime_session, seed_fattura, tmp_path):
    stale = tmp_path / "stale.xml"
    stale.write_text("<not-a-fattura/>", encoding="utf-8")
    seed_fattura.xml_path = str(stale)
    runtime_session.commit()

    path = _prepare_transmission(seed_fattura, _service(), signed=False)

    assert isinstance(path, Path)
    content = path.read_text(encoding="utf-8")
    assert FatturaPAValidator().validate(content)[0]
    assert content.strip() == FatturaPABuilder(get_settings()).build(seed_fattura).strip()


def test_signed_send_requires_a_signed_file(runtime_session, seed_fattura):
    assert _prepare_transmission(seed_fattura, _service(), signed=True) == (
        "No signed XML for this invoice: sign it first (sign_invoice_xml)"
    )


def _signed(runtime_session, fattura: Fattura, tmp_path: Path) -> Path:
    xml = tmp_path / "signed-source.xml"
    xml.write_text(FatturaPABuilder(get_settings()).build(fattura), encoding="utf-8")
    p7m = tmp_path / "signed-source.xml.p7m"
    p7m.write_bytes(b"signature")
    fattura.xml_path, fattura.xml_firmato_path = str(xml), str(p7m)
    runtime_session.commit()
    return p7m


def test_signed_send_uses_the_p7m_when_xml_matches(runtime_session, seed_fattura, tmp_path):
    p7m = _signed(runtime_session, seed_fattura, tmp_path)

    assert _prepare_transmission(seed_fattura, _service(), signed=True) == p7m


def test_signed_send_refuses_an_invoice_changed_after_signing(
    runtime_session, seed_fattura, tmp_path
):
    _signed(runtime_session, seed_fattura, tmp_path)
    riga = seed_fattura.righe[0]
    runtime_session.add(
        RigaFattura(
            fattura_id=seed_fattura.id,
            numero_riga=2,
            descrizione="Aggiunta dopo la firma",
            quantita=riga.quantita,
            prezzo_unitario=riga.prezzo_unitario,
            unita_misura=riga.unita_misura,
            aliquota_iva=riga.aliquota_iva,
            imponibile=riga.imponibile,
            iva=riga.iva,
            totale=riga.totale,
        )
    )
    runtime_session.commit()
    runtime_session.refresh(seed_fattura)

    assert _prepare_transmission(seed_fattura, _service(), signed=True) == (
        "The invoice changed after signing: generate the XML and sign it again"
    )
