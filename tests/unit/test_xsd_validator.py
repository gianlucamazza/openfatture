"""Unit tests for XSD validator."""

from pathlib import Path

import pytest

from openfatture.sdi.validator.xsd_validator import FatturaPAValidator

pytestmark = pytest.mark.unit


class TestBundledSchemas:
    """Tests for bundled XSD schemas and offline validation."""

    def test_bundled_schema_loads_successfully(self):
        """Test that bundled FatturaPA schema loads without errors."""
        validator = FatturaPAValidator()
        validator.load_schema()

        assert validator._schema is not None
        assert validator._use_bundled is True

    def test_validate_minimal_fatturapa_xml(self):
        """Test validation of minimal valid FatturaPA XML using bundled schema."""
        validator = FatturaPAValidator()

        # Load minimal FatturaPA fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "minimal_fatturapa.xml"
        xml_content = fixture_path.read_text(encoding="utf-8")

        # Validate - should succeed with bundled schema (offline)
        is_valid, error = validator.validate(xml_content)

        assert is_valid is True, f"Validation failed: {error}"
        assert error is None

    def test_bundled_schema_resolves_xmldsig_offline(self):
        """Test that xmldsig-core-schema.xsd is resolved from bundled resources."""
        # This test verifies the fix for the original issue:
        # xmldsig import should resolve locally, not via HTTP
        validator = FatturaPAValidator()

        # Load schema - should not require network access
        # If xmldsig is not properly bundled, this would fail
        validator.load_schema()

        # Schema should have loaded successfully
        assert validator._schema is not None

        # Now validate a minimal XML to ensure schema is fully functional
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<p:FatturaElettronica versione="FPR12"
    xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <FatturaElettronicaHeader>
    <DatiTrasmissione>
      <IdTrasmittente><IdPaese>IT</IdPaese><IdCodice>01234567890</IdCodice></IdTrasmittente>
      <ProgressivoInvio>00001</ProgressivoInvio>
      <FormatoTrasmissione>FPR12</FormatoTrasmissione>
      <CodiceDestinatario>0000000</CodiceDestinatario>
    </DatiTrasmissione>
    <CedentePrestatore>
      <DatiAnagrafici>
        <IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>01234567890</IdCodice></IdFiscaleIVA>
        <Anagrafica><Denominazione>Test</Denominazione></Anagrafica>
        <RegimeFiscale>RF01</RegimeFiscale>
      </DatiAnagrafici>
      <Sede><Indirizzo>Via Test 1</Indirizzo><CAP>00100</CAP>
        <Comune>Roma</Comune><Provincia>RM</Provincia><Nazione>IT</Nazione></Sede>
    </CedentePrestatore>
    <CessionarioCommittente>
      <DatiAnagrafici>
        <CodiceFiscale>RSSMRA85M01H501U</CodiceFiscale>
        <Anagrafica><Denominazione>Customer</Denominazione></Anagrafica>
      </DatiAnagrafici>
      <Sede><Indirizzo>Via Cliente 2</Indirizzo><CAP>00200</CAP>
        <Comune>Milano</Comune><Provincia>MI</Provincia><Nazione>IT</Nazione></Sede>
    </CessionarioCommittente>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>
        <TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa>
        <Data>2025-01-15</Data><Numero>1</Numero>
      </DatiGeneraliDocumento>
    </DatiGenerali>
    <DatiBeniServizi>
      <DettaglioLinee>
        <NumeroLinea>1</NumeroLinea><Descrizione>Test</Descrizione>
        <Quantita>1.00</Quantita><UnitaMisura>pz</UnitaMisura>
        <PrezzoUnitario>100.00</PrezzoUnitario><PrezzoTotale>100.00</PrezzoTotale>
        <AliquotaIVA>22.00</AliquotaIVA>
      </DettaglioLinee>
      <DatiRiepilogo>
        <AliquotaIVA>22.00</AliquotaIVA><ImponibileImporto>100.00</ImponibileImporto>
        <Imposta>22.00</Imposta><EsigibilitaIVA>I</EsigibilitaIVA>
      </DatiRiepilogo>
    </DatiBeniServizi>
  </FatturaElettronicaBody>
</p:FatturaElettronica>"""

        is_valid, error = validator.validate(minimal_xml)
        assert is_valid is True, f"Validation failed: {error}"


class TestFatturaPAValidator:
    """Tests for FatturaPA XSD validator."""

    def test_init_default_uses_bundled(self):
        """Test validator initialization defaults to bundled schemas."""
        validator = FatturaPAValidator()

        assert validator.xsd_path is None
        assert validator._use_bundled is True

    def test_init_custom_path(self, tmp_path):
        """Test validator initialization with custom XSD path."""
        custom_path = tmp_path / "custom.xsd"
        validator = FatturaPAValidator(xsd_path=custom_path)

        assert validator.xsd_path == custom_path
        assert validator._use_bundled is False

    def test_load_schema_custom_file_not_found(self, tmp_path):
        """Test load_schema raises FileNotFoundError if custom XSD missing."""
        custom_path = tmp_path / "nonexistent.xsd"
        validator = FatturaPAValidator(xsd_path=custom_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            validator.load_schema()

        assert "Either use the bundled schema" in str(exc_info.value)

    def test_load_schema_custom_success(self, tmp_path):
        """Test successful schema loading with custom path."""
        # Create minimal valid XSD
        xsd_file = tmp_path / "custom.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator(xsd_path=xsd_file)
        validator.load_schema()

        assert validator._schema is not None

    def test_validate_with_bundled_schema_invalid_xml(self):
        """Test validate() with bundled schema catches validation errors."""
        validator = FatturaPAValidator()

        # Invalid XML (not matching FatturaPA schema)
        xml_content = "<?xml version='1.0'?><root>test</root>"
        is_valid, error = validator.validate(xml_content)

        assert is_valid is False
        assert "Validation error" in error

    def test_validate_invalid_xml_syntax(self):
        """Test validate() catches XML syntax errors."""
        validator = FatturaPAValidator()

        # Invalid XML (missing closing tag)
        invalid_xml = "<?xml version='1.0'?><root>test"
        is_valid, error = validator.validate(invalid_xml)

        assert is_valid is False
        assert "XML syntax error" in error

    def test_validate_valid_xml_with_custom_schema(self, tmp_path):
        """Test validate() with valid XML against custom schema."""
        # Create valid XSD
        xsd_file = tmp_path / "custom.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator(xsd_path=xsd_file)

        # Valid XML matching schema
        valid_xml = "<?xml version='1.0'?><root>test content</root>"
        is_valid, error = validator.validate(valid_xml)

        assert is_valid is True
        assert error is None

    def test_validate_invalid_against_custom_schema(self, tmp_path):
        """Test validate() detects XML that doesn't match custom schema."""
        # Create XSD that requires specific structure
        xsd_file = tmp_path / "custom.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="required" type="xs:string"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator(xsd_path=xsd_file)

        # XML missing required element
        invalid_xml = "<?xml version='1.0'?><root><wrong>element</wrong></root>"
        is_valid, error = validator.validate(invalid_xml)

        assert is_valid is False
        assert "Validation error" in error

    def test_validate_file_not_found(self, tmp_path):
        """Test validate_file() with non-existent file."""
        validator = FatturaPAValidator()
        non_existent = tmp_path / "nonexistent.xml"

        is_valid, error = validator.validate_file(non_existent)

        assert is_valid is False
        assert "File not found" in error

    def test_validate_file_success(self):
        """Test validate_file() with existing XML file."""
        validator = FatturaPAValidator()

        # Use the fixture file
        fixture_path = Path(__file__).parent.parent / "fixtures" / "minimal_fatturapa.xml"

        is_valid, error = validator.validate_file(fixture_path)

        assert is_valid is True, f"Validation failed: {error}"
        assert error is None

    def test_schema_cached_after_first_load(self):
        """Test that schema is cached and not reloaded on subsequent validations."""
        validator = FatturaPAValidator()

        # Load fixture
        fixture_path = Path(__file__).parent.parent / "fixtures" / "minimal_fatturapa.xml"
        xml_content = fixture_path.read_text(encoding="utf-8")

        # First validation loads schema
        validator.validate(xml_content)
        schema_obj = validator._schema

        # Second validation uses cached schema
        validator.validate(xml_content)

        assert validator._schema is schema_obj  # Same object
