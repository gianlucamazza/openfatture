"""Unit tests for XSD validator."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.sdi.validator.xsd_validator import FatturaPAValidator, download_xsd_schema

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


class TestDownloadXSDSchema:
    """Tests for download_xsd_schema function."""

    @patch("openfatture.platform.config.get_settings")
    def test_download_xsd_schema_creates_dir(self, mock_settings, tmp_path):
        """Test that download_xsd_schema creates schema directory."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        schema_dir = tmp_path / "schemas"
        assert not schema_dir.exists()

        try:
            download_xsd_schema()
        except FileNotFoundError:
            pass  # Expected

        assert schema_dir.exists()

    @patch("openfatture.platform.config.get_settings")
    def test_download_xsd_schema_file_exists(self, mock_settings, tmp_path):
        """Test download_xsd_schema returns existing file."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create existing schema file
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"
        xsd_file.write_text("<?xml version='1.0'?><schema/>", encoding="utf-8")

        result = download_xsd_schema()

        assert result == xsd_file
        assert result.exists()

    @patch("openfatture.platform.config.get_settings")
    def test_download_xsd_schema_file_not_exists(self, mock_settings, tmp_path):
        """Test download_xsd_schema raises error with instructions if file missing."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        with pytest.raises(FileNotFoundError) as exc_info:
            download_xsd_schema()

        error_msg = str(exc_info.value)
        assert "XSD schema not found" in error_msg
        assert "download manually" in error_msg
        assert "fatturapa.gov.it" in error_msg
        assert "FatturaPA_v1.2.2.xsd" in error_msg

    @patch("openfatture.platform.config.get_settings")
    @patch("urllib.request.urlopen")
    def test_download_xsd_schema_auto_download_success(self, mock_urlopen, mock_settings, tmp_path):
        """Test auto_download successfully downloads schema."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b"<?xml version='1.0'?><schema/>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        result = download_xsd_schema(auto_download=True)

        expected_path = tmp_path / "schemas" / "FatturaPA_v1.2.2.xsd"
        assert result == expected_path
        assert result.exists()
        assert result.read_text() == "<?xml version='1.0'?><schema/>"

        # Verify download was called with correct URL
        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args[0][0]
        assert "fatturapa.gov.it" in call_args
        assert "FatturaPA_v1.2.2.xsd" in call_args

    @patch("openfatture.platform.config.get_settings")
    @patch("urllib.request.urlopen")
    def test_download_xsd_schema_network_error(self, mock_urlopen, mock_settings, tmp_path):
        """Test auto_download handles network errors."""
        import urllib.error

        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Mock network error
        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        with pytest.raises(urllib.error.URLError) as exc_info:
            download_xsd_schema(auto_download=True)

        error_msg = str(exc_info.value)
        assert "Failed to download XSD schema" in error_msg
        assert "fatturapa.gov.it" in error_msg

    @patch("openfatture.platform.config.get_settings")
    @patch("urllib.request.urlopen")
    def test_download_xsd_schema_write_error(self, mock_urlopen, mock_settings, tmp_path):
        """Test auto_download handles file write errors."""
        mock_settings_instance = Mock()
        # Use read-only path to trigger write error
        mock_settings_instance.data_dir = tmp_path / "readonly"
        mock_settings.return_value = mock_settings_instance

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b"<?xml version='1.0'?><schema/>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        # Create readonly directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        # Note: This test may not work perfectly on all systems
        # On Windows, file permissions work differently

        # Instead, we'll mock write_bytes to raise an error
        with patch("pathlib.Path.write_bytes", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError) as exc_info:
                download_xsd_schema(auto_download=True)

            error_msg = str(exc_info.value)
            assert "Failed to write XSD schema" in error_msg
