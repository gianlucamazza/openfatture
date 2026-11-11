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

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.config import app

# Under the default 80-column terminal Rich truncates table cells, which would
# make substring assertions ("Not set", "Set", the API key) flaky. A fixed wide
# width keeps the rendered tokens intact and deterministic.
runner = CliRunner(env={"COLUMNS": "220"})
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
    """``config set`` writes only the given key; secrets go to the secret store."""

    @pytest.fixture(autouse=True)
    def _isolated(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path))
        monkeypatch.setenv("OPENFATTURE_SECRET_BACKEND", "file")
        for name in ("AI_PROVIDER", "AI_API_KEY", "PEC_PASSWORD", "AI_CHAT_MAX_TOKENS"):
            monkeypatch.delenv(name, raising=False)
        self.config = tmp_path / "config.toml"
        self.credentials = tmp_path / "credentials.toml"

    def test_set_writes_only_the_key_and_keeps_comments(self):
        self.config.write_text('# personal note\nai_model = "kept"\n')

        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 0, result.stdout
        assert "Set ai_provider = anthropic" in result.stdout
        assert self.config.read_text() == (
            '# personal note\nai_model = "kept"\nai_provider = "anthropic"\n'
        )
        assert oct(self.config.stat().st_mode & 0o777) == "0o600"

    def test_set_keeps_spaces_and_coerces_types(self):
        assert runner.invoke(app, ["set", "cedente_indirizzo", "Via Roma 123"]).exit_code == 0
        assert runner.invoke(app, ["set", "ai_chat_max_tokens", "465"]).exit_code == 0
        assert runner.invoke(app, ["set", "ai_chat_enabled", "false"]).exit_code == 0

        import tomllib

        stored = tomllib.loads(self.config.read_text())
        assert stored == {
            "cedente_indirizzo": "Via Roma 123",
            "ai_chat_max_tokens": 465,
            "ai_chat_enabled": False,
        }

    def test_set_rejects_invalid_values(self):
        result = runner.invoke(app, ["set", "ai_chat_max_tokens", "many"])

        assert result.exit_code == 1
        assert "Invalid value for ai_chat_max_tokens" in result.stdout
        assert not self.config.exists()

    def test_secret_goes_to_store_not_config(self):
        self.config.write_text('ai_api_key = "old-plaintext"\n')

        result = runner.invoke(app, ["set", "ai_api_key", "sk-new-secret"])

        assert result.exit_code == 0, result.stdout
        assert "sk-new-secret" not in result.stdout
        assert "credentials file" in result.stdout
        assert "ai_api_key" not in self.config.read_text()
        assert "sk-new-secret" in self.credentials.read_text()
        assert oct(self.credentials.stat().st_mode & 0o777) == "0o600"

    def test_environment_override_is_reported(self, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "ollama")

        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 0
        assert "environment variable" in result.stdout

    def test_set_reports_write_errors(self, monkeypatch):
        def fail(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("openfatture.cli.commands.config.update_config", fail)
        result = runner.invoke(app, ["set", "ai_provider", "anthropic"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_set_config_invalid_key(self):
        result = runner.invoke(app, ["set", "nonexistent_key", "value"])

        assert result.exit_code == 1
        assert "Invalid configuration key" in result.stdout

    def test_set_config_requires_key_and_value(self):
        assert runner.invoke(app, ["set"]).exit_code != 0
        assert runner.invoke(app, ["set", "ai_provider"]).exit_code != 0

    def test_unset_removes_value_and_secret(self):
        runner.invoke(app, ["set", "ai_provider", "anthropic"])
        runner.invoke(app, ["set", "pec_password", "pw"])

        assert "Removed ai_provider" in runner.invoke(app, ["unset", "ai_provider"]).stdout
        assert "Removed pec_password" in runner.invoke(app, ["unset", "pec_password"]).stdout
        assert "was not set" in runner.invoke(app, ["unset", "pec_password"]).stdout
        assert "ai_provider" not in self.config.read_text()
        assert "pec_password" not in self.credentials.read_text()


class TestMigrateConfigCommand:
    @pytest.fixture(autouse=True)
    def _isolated(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path / "profile"))
        monkeypatch.setenv("OPENFATTURE_SECRET_BACKEND", "file")
        self.profile = tmp_path / "profile"
        self.profile.mkdir()
        self.config = self.profile / "config.toml"
        self.dotenv = tmp_path / ".env"

    def test_moves_plaintext_secrets_out_of_config(self):
        self.config.write_text('ai_model = "m"\nai_api_key = "sk-plain"\n')

        result = runner.invoke(app, ["migrate"])

        assert result.exit_code == 0, result.stdout
        assert "Moved to credentials file: ai_api_key" in result.stdout
        assert self.config.read_text() == 'ai_model = "m"\n'
        assert "sk-plain" in (self.profile / "credentials.toml").read_text()

    def test_imports_env_file_without_overwriting(self):
        self.config.write_text('ai_model = "deepseek"\n')
        self.dotenv.write_text(
            "AI_PROVIDER=ollama\nAI_MODEL=llama3.2\nPEC_PASSWORD=pw\n"
            "CEDENTE_CAP=25128\nPEC_SMTP_PORT=abc\nUNRELATED=1\n"
        )

        result = runner.invoke(app, ["migrate", "--env-file", str(self.dotenv)])

        assert result.exit_code == 0, result.stdout
        import tomllib

        stored = tomllib.loads(self.config.read_text())
        assert stored == {"ai_model": "deepseek", "ai_provider": "ollama", "cedente_cap": "25128"}
        assert "Already set, not overwritten: ai_model" in result.stdout
        assert "Invalid value for PEC_SMTP_PORT" in result.stdout
        assert "pw" in (self.profile / "credentials.toml").read_text()
        assert self.dotenv.exists()

    def test_env_file_keeps_stored_secrets_and_equal_values(self):
        self.config.write_text('ai_model = "same"\n')
        assert runner.invoke(app, ["set", "pec_password", "old"]).exit_code == 0
        self.dotenv.write_text("AI_MODEL=same\nPEC_PASSWORD=new\nAI_API_KEY=\n")

        result = runner.invoke(app, ["migrate", "--env-file", str(self.dotenv)])

        assert result.exit_code == 0, result.stdout
        assert "Already set, not overwritten: pec_password" in result.stdout
        assert "ai_model" not in result.stdout
        assert self.config.read_text() == 'ai_model = "same"\n'
        credentials = (self.profile / "credentials.toml").read_text()
        assert "old" in credentials
        assert "new" not in credentials
        assert "ai_api_key" not in credentials

    def test_nothing_to_migrate(self):
        result = runner.invoke(app, ["migrate"])

        assert result.exit_code == 0
        assert "Nothing to migrate." in result.stdout
