"""Tests for config CLI commands.

The ``config show`` command renders a Rich table through the i18n ``_()`` helper,
so the locale is pinned to English to make label assertions deterministic, and a
wide terminal width is forced so Rich does not truncate the rendered cells.

``config set`` writes through the real ``save_config`` seam to a TOML file under
``dirs.user_config_dir``; the tests patch those seams (not a legacy ``.env``
append) so they exercise the command's actual behaviour: flat attribute keys are
validated against ``get_settings()``, type-converted from the current value, and
persisted via ``save_config``.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.config import app


class _WideCliRunner(CliRunner):
    """CliRunner that renders Rich output at a wide terminal width.

    Under the default 80-column terminal Rich truncates table cells, which would
    make substring assertions ("Not set", "Set", the API key) flaky. A fixed wide
    width keeps the rendered tokens intact and deterministic.
    """

    def invoke(self, *args, **kwargs):  # type: ignore[override]
        env = {"COLUMNS": "220", **(kwargs.pop("env", None) or {})}
        return super().invoke(*args, env=env, **kwargs)


runner = _WideCliRunner()
pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _english_locale():
    """Pin the locale to English so label assertions are deterministic."""
    from openfatture.i18n import get_locale, set_locale

    previous = get_locale()
    set_locale("en")
    try:
        yield
    finally:
        set_locale(previous)


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
    """Test 'config set' command.

    ``config set`` validates the key against the live settings object, type-coerces
    the value from the current attribute, and persists via ``save_config`` to a TOML
    file. ``dirs`` and ``save_config`` are patched at their definition modules because
    the command imports them locally inside the function body.
    """

    @patch("openfatture.cli.wizard.save_config")
    @patch("openfatture.utils.config.dirs")
    def test_set_config_success(self, mock_dirs, mock_save_config, tmp_path):
        """Test successful configuration setting for a valid string key."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 0
        assert "Set ai_provider = anthropic" in result.stdout
        assert "Saved to" in result.stdout

        # The updated settings object is persisted to the config file.
        mock_save_config.assert_called_once()
        saved_settings, saved_path = mock_save_config.call_args[0]
        assert saved_settings.ai_provider == "anthropic"
        assert Path(saved_path) == tmp_path / "config.toml"

    @patch("openfatture.cli.wizard.save_config")
    @patch("openfatture.utils.config.dirs")
    def test_set_config_updates_string_attribute(self, mock_dirs, mock_save_config, tmp_path):
        """Test that config set updates a flat string attribute on settings."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "cedente_denominazione", "New Company"])

        assert result.exit_code == 0
        assert "Set cedente_denominazione = New Company" in result.stdout

        # The new value is applied to the settings object before saving.
        saved_settings = mock_save_config.call_args[0][0]
        assert saved_settings.cedente_denominazione == "New Company"

    @patch("openfatture.cli.wizard.save_config")
    @patch("openfatture.utils.config.dirs")
    def test_set_config_with_spaces_in_value(self, mock_dirs, mock_save_config, tmp_path):
        """Test setting config with spaces in value."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "cedente_indirizzo", "Via Roma 123"])

        assert result.exit_code == 0
        assert "Via Roma 123" in result.stdout

        saved_settings = mock_save_config.call_args[0][0]
        assert saved_settings.cedente_indirizzo == "Via Roma 123"

    @patch("openfatture.cli.wizard.save_config", side_effect=PermissionError("Permission denied"))
    @patch("openfatture.utils.config.dirs")
    def test_set_config_permission_error(self, mock_dirs, mock_save_config, tmp_path):
        """Test config set when persistence fails with a permission error."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    @patch("openfatture.cli.wizard.save_config", side_effect=OSError("File not found"))
    @patch("openfatture.utils.config.dirs")
    def test_set_config_file_error(self, mock_dirs, mock_save_config, tmp_path):
        """Test config set when persistence fails with a file error."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_set_config_invalid_key(self):
        """Test that config set rejects keys that do not exist on settings."""
        result = runner.invoke(app, ["set", "nonexistent_key", "value"])

        assert result.exit_code == 1
        assert "Invalid configuration key" in result.stdout

    def test_set_config_requires_key_and_value(self):
        """Test that config set requires both key and value arguments."""
        # Missing both arguments
        result = runner.invoke(app, ["set"])
        assert result.exit_code != 0

        # Missing value argument
        result = runner.invoke(app, ["set", "ai_provider"])
        assert result.exit_code != 0

    @patch("openfatture.cli.wizard.save_config")
    @patch("openfatture.utils.config.dirs")
    def test_set_config_with_numeric_value(self, mock_dirs, mock_save_config, tmp_path):
        """Test setting config with numeric value coerces from the int attribute."""
        mock_dirs.user_config_dir = tmp_path

        result = runner.invoke(app, ["set", "ai_chat_max_tokens", "465"])

        assert result.exit_code == 0
        assert "465" in result.stdout

        # An integer-typed setting is coerced to int before saving.
        saved_settings = mock_save_config.call_args[0][0]
        assert saved_settings.ai_chat_max_tokens == 465
        assert isinstance(saved_settings.ai_chat_max_tokens, int)
