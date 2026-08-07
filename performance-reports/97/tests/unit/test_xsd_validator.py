"""Unit tests for XSD validator."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from openfatture.sdi.validator.xsd_validator import FatturaPAValidator, download_xsd_schema

pytestmark = pytest.mark.unit


class TestFatturaPAValidator:
    """Tests for FatturaPA XSD validator."""

    @patch("openfatture.utils.config.get_settings")
    def test_init_default_path(self, mock_settings, tmp_path):
        """Test validator initialization with default XSD path."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        validator = FatturaPAValidator()

        expected_path = tmp_path / "schemas" / "FatturaPA_v1.2.2.xsd"
        assert validator.xsd_path == expected_path

    def test_init_custom_path(self, tmp_path):
        """Test validator initialization with custom XSD path."""
        custom_path = tmp_path / "custom.xsd"
        validator = FatturaPAValidator(xsd_path=custom_path)

        assert validator.xsd_path == custom_path

    @patch("openfatture.utils.config.get_settings")
    def test_load_schema_file_not_found(self, mock_settings, tmp_path):
        """Test load_schema raises FileNotFoundError if XSD missing."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        validator = FatturaPAValidator()

        with pytest.raises(FileNotFoundError) as exc_info:
            validator.load_schema()

        assert "XSD schema not found" in str(exc_info.value)
        assert "Download from:" in str(exc_info.value)

    @patch("openfatture.utils.config.get_settings")
    def test_load_schema_success(self, mock_settings, tmp_path):
        """Test successful schema loading."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create minimal valid XSD
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator()
        validator.load_schema()

        assert validator._schema is not None

    @patch("openfatture.utils.config.get_settings")
    def test_validate_loads_schema_automatically(self, mock_settings, tmp_path):
        """Test validate() loads schema automatically if not loaded."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        validator = FatturaPAValidator()

        # XSD file doesn't exist
        xml_content = "<?xml version='1.0'?><root>test</root>"
        is_valid, error = validator.validate(xml_content)

        assert is_valid is False
        assert "XSD schema not found" in error

    @patch("openfatture.utils.config.get_settings")
    def test_validate_invalid_xml_syntax(self, mock_settings, tmp_path):
        """Test validate() catches XML syntax errors."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create valid XSD
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator()

        # Invalid XML (missing closing tag)
        invalid_xml = "<?xml version='1.0'?><root>test"
        is_valid, error = validator.validate(invalid_xml)

        assert is_valid is False
        assert "XML syntax error" in error

    @patch("openfatture.utils.config.get_settings")
    def test_validate_valid_xml(self, mock_settings, tmp_path):
        """Test validate() with valid XML against schema."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create valid XSD
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator()

        # Valid XML matching schema
        valid_xml = "<?xml version='1.0'?><root>test content</root>"
        is_valid, error = validator.validate(valid_xml)

        assert is_valid is True
        assert error is None

    @patch("openfatture.utils.config.get_settings")
    def test_validate_invalid_against_schema(self, mock_settings, tmp_path):
        """Test validate() detects XML that doesn't match schema."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create XSD that requires specific structure
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

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

        validator = FatturaPAValidator()

        # XML missing required element
        invalid_xml = "<?xml version='1.0'?><root><wrong>element</wrong></root>"
        is_valid, error = validator.validate(invalid_xml)

        assert is_valid is False
        assert "Validation error" in error

    @patch("openfatture.utils.config.get_settings")
    def test_validate_file_not_found(self, mock_settings, tmp_path):
        """Test validate_file() with non-existent file."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        validator = FatturaPAValidator()
        non_existent = tmp_path / "nonexistent.xml"

        is_valid, error = validator.validate_file(non_existent)

        assert is_valid is False
        assert "File not found" in error

    @patch("openfatture.utils.config.get_settings")
    def test_validate_file_success(self, mock_settings, tmp_path):
        """Test validate_file() with existing XML file."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create valid XSD
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        # Create valid XML file
        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<?xml version='1.0'?><root>test</root>", encoding="utf-8")

        validator = FatturaPAValidator()
        is_valid, error = validator.validate_file(xml_file)

        assert is_valid is True
        assert error is None

    @patch("openfatture.utils.config.get_settings")
    def test_schema_cached_after_first_load(self, mock_settings, tmp_path):
        """Test that schema is cached and not reloaded on subsequent validations."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        # Create valid XSD
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir(parents=True)
        xsd_file = schema_dir / "FatturaPA_v1.2.2.xsd"

        xsd_content = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>"""
        xsd_file.write_text(xsd_content, encoding="utf-8")

        validator = FatturaPAValidator()

        # First validation loads schema
        xml_content = "<?xml version='1.0'?><root>test1</root>"
        validator.validate(xml_content)
        schema_obj = validator._schema

        # Second validation uses cached schema
        xml_content2 = "<?xml version='1.0'?><root>test2</root>"
        validator.validate(xml_content2)

        assert validator._schema is schema_obj  # Same object

    @patch("openfatture.utils.config.get_settings")
    def test_get_default_xsd_path_structure(self, mock_settings, tmp_path):
        """Test that default XSD path follows expected structure."""
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path
        mock_settings.return_value = mock_settings_instance

        path = FatturaPAValidator._get_default_xsd_path()

        assert path == tmp_path / "schemas" / "FatturaPA_v1.2.2.xsd"
        assert path.name == "FatturaPA_v1.2.2.xsd"
        assert path.parent.name == "schemas"


class TestDownloadXSDSchema:
    """Tests for download_xsd_schema function."""

    @patch("openfatture.utils.config.get_settings")
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

    @patch("openfatture.utils.config.get_settings")
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

    @patch("openfatture.utils.config.get_settings")
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

    @patch("openfatture.utils.config.get_settings")
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

    @patch("openfatture.utils.config.get_settings")
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

    @patch("openfatture.utils.config.get_settings")
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
