"""
Tests for config CLI commands.
"""

from unittest.mock import Mock, mock_open, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.config import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestShowConfigCommand:
    """Test 'config show' command."""

    @patch("openfatture.cli.commands.config.get_settings")
    def test_show_config_displays_all_settings(self, mock_settings):
        """Test that config show displays all configuration."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.app_version = "1.0.0"
        mock_settings_instance.debug = False
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings_instance.data_dir = "/data"
        mock_settings_instance.archivio_dir = "/archivio"
        mock_settings_instance.certificates_dir = "/certs"
        mock_settings_instance.cedente_denominazione = "Test Company"
        mock_settings_instance.cedente_partita_iva = "12345678901"
        mock_settings_instance.cedente_codice_fiscale = "RSSMRA80A01H501U"
        mock_settings_instance.cedente_regime_fiscale = "RF19"
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_smtp_server = "smtp.pec.aruba.it"
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"
        mock_settings_instance.ai_provider = "anthropic"
        mock_settings_instance.ai_model = "claude-3-5-sonnet-20241022"
        mock_settings_instance.ai_api_key = "sk-ant-test"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        assert "OpenFatture Configuration" in result.stdout
        assert "1.0.0" in result.stdout
        assert "Test Company" in result.stdout
        assert "12345678901" in result.stdout
        assert "test@pec.it" in result.stdout
        assert "anthropic" in result.stdout

    @patch("openfatture.cli.commands.config.get_settings")
    def test_show_config_shows_not_set_for_missing_values(self, mock_settings):
        """Test that config show displays 'Not set' for missing values."""
        # Setup settings mock with missing values
        mock_settings_instance = Mock()
        mock_settings_instance.app_version = "1.0.0"
        mock_settings_instance.debug = False
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings_instance.data_dir = "/data"
        mock_settings_instance.archivio_dir = "/archivio"
        mock_settings_instance.certificates_dir = "/certs"
        mock_settings_instance.cedente_denominazione = None
        mock_settings_instance.cedente_partita_iva = None
        mock_settings_instance.cedente_codice_fiscale = None
        mock_settings_instance.cedente_regime_fiscale = "RF19"
        mock_settings_instance.pec_address = None
        mock_settings_instance.pec_smtp_server = "smtp.pec.aruba.it"
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"
        mock_settings_instance.ai_provider = "anthropic"
        mock_settings_instance.ai_model = "claude-3-5-sonnet-20241022"
        mock_settings_instance.ai_api_key = None
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        assert "Not set" in result.stdout

    @patch("openfatture.cli.commands.config.get_settings")
    def test_show_config_masks_ai_api_key(self, mock_settings):
        """Test that config show masks AI API key."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.app_version = "1.0.0"
        mock_settings_instance.debug = False
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings_instance.data_dir = "/data"
        mock_settings_instance.archivio_dir = "/archivio"
        mock_settings_instance.certificates_dir = "/certs"
        mock_settings_instance.cedente_denominazione = "Test Company"
        mock_settings_instance.cedente_partita_iva = "12345678901"
        mock_settings_instance.cedente_codice_fiscale = "RSSMRA80A01H501U"
        mock_settings_instance.cedente_regime_fiscale = "RF19"
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_smtp_server = "smtp.pec.aruba.it"
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"
        mock_settings_instance.ai_provider = "anthropic"
        mock_settings_instance.ai_model = "claude-3-5-sonnet-20241022"
        mock_settings_instance.ai_api_key = "sk-ant-secret-key-12345"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        # API key should not be shown in plain text
        assert "sk-ant-secret-key-12345" not in result.stdout
        assert "Set" in result.stdout

    @patch("openfatture.cli.commands.config.get_settings")
    def test_show_config_shows_debug_mode(self, mock_settings):
        """Test that config show displays debug mode status."""
        # Setup settings mock with debug enabled
        mock_settings_instance = Mock()
        mock_settings_instance.app_version = "1.0.0"
        mock_settings_instance.debug = True
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings_instance.data_dir = "/data"
        mock_settings_instance.archivio_dir = "/archivio"
        mock_settings_instance.certificates_dir = "/certs"
        mock_settings_instance.cedente_denominazione = "Test"
        mock_settings_instance.cedente_partita_iva = "12345678901"
        mock_settings_instance.cedente_codice_fiscale = "RSSMRA80A01H501U"
        mock_settings_instance.cedente_regime_fiscale = "RF19"
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_smtp_server = "smtp.pec.aruba.it"
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"
        mock_settings_instance.ai_provider = "anthropic"
        mock_settings_instance.ai_model = "claude-3-5-sonnet-20241022"
        mock_settings_instance.ai_api_key = None
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["show"])

        assert result.exit_code == 0
        assert "True" in result.stdout


class TestReloadConfigCommand:
    """Test 'config reload' command."""

    @patch("openfatture.cli.commands.config.reload_settings")
    def test_reload_config_success(self, mock_reload):
        """Test successful configuration reload."""
        result = runner.invoke(app, ["reload"])

        assert result.exit_code == 0
        assert "Configuration reloaded" in result.stdout
        mock_reload.assert_called_once()


class TestSetConfigCommand:
    """Test 'config set' command."""

    @patch("builtins.open", new_callable=mock_open)
    def test_set_config_success(self, mock_file):
        """Test successful configuration setting."""
        result = runner.invoke(app, ["set", "pec.address", "newemail@pec.it"])

        assert result.exit_code == 0
        assert "Set pec.address = newemail@pec.it" in result.stdout
        assert "Restart CLI or run 'config reload'" in result.stdout

        # Verify file operations
        mock_file.assert_called_once_with(".env", "a")
        handle = mock_file()
        handle.write.assert_called_once()

        # Check what was written
        written_content = handle.write.call_args[0][0]
        assert "PEC_ADDRESS" in written_content
        assert "newemail@pec.it" in written_content

    @patch("builtins.open", new_callable=mock_open)
    def test_set_config_converts_key_format(self, mock_file):
        """Test that config set converts keys to proper format."""
        result = runner.invoke(app, ["set", "cedente.denominazione", "New Company"])

        assert result.exit_code == 0
        assert "Set cedente.denominazione = New Company" in result.stdout

        # Check that key was converted to uppercase with underscores
        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        assert "CEDENTE_DENOMINAZIONE" in written_content

    @patch("builtins.open", new_callable=mock_open)
    def test_set_config_with_spaces_in_value(self, mock_file):
        """Test setting config with spaces in value."""
        result = runner.invoke(app, ["set", "cedente.indirizzo", "Via Roma 123"])

        assert result.exit_code == 0
        assert "Via Roma 123" in result.stdout

        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        assert "Via Roma 123" in written_content

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_set_config_permission_error(self, mock_file):
        """Test config set with permission error."""
        result = runner.invoke(app, ["set", "pec.address", "test@pec.it"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_set_config_file_error(self, mock_file):
        """Test config set with file error."""
        result = runner.invoke(app, ["set", "pec.address", "test@pec.it"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_set_config_requires_key_and_value(self):
        """Test that config set requires both key and value arguments."""
        # Missing both arguments
        result = runner.invoke(app, ["set"])
        assert result.exit_code != 0

        # Missing value argument
        result = runner.invoke(app, ["set", "pec.address"])
        assert result.exit_code != 0

    @patch("builtins.open", new_callable=mock_open)
    def test_set_config_with_numeric_value(self, mock_file):
        """Test setting config with numeric value."""
        result = runner.invoke(app, ["set", "pec.smtp.port", "465"])

        assert result.exit_code == 0
        assert "465" in result.stdout

        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        assert "PEC_SMTP_PORT" in written_content
        assert "465" in written_content
