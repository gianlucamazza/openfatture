"""
Tests for init CLI command.
"""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.init import app

runner = CliRunner()
pytestmark = pytest.mark.unit

# Test constants - use secure test values
TEST_PEC_PASSWORD = "test_pec_password_secure_123"
TEST_CODICE_DESTINATARIO = "TESTCODE"
TEST_BIC_SWIFT = "TESTBIC123"


@pytest.fixture(autouse=True)
def isolated_setup_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path / "profile"))


class TestInitCommand:
    """Test 'init' command."""

    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_non_interactive(self, mock_settings, mock_init_db, tmp_path):
        """Test non-interactive initialization."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["--no-interactive"])

        assert result.exit_code == 0
        assert "Configurazione di OpenFatture" in result.stdout
        assert "Creazione delle directory" in result.stdout
        assert "Inizializzazione del database" in result.stdout
        assert "Configurazione completata" in result.stdout

        # Verify init_db was called
        mock_init_db.assert_called_once_with(f"sqlite:///{tmp_path / 'test.db'}")

    @pytest.mark.skip(
        reason="Complex interactive test - requires working directory mocking refactor"
    )
    @patch("openfatture.cli.commands.init.Prompt")
    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_new_env(
        self, mock_settings, mock_init_db, mock_confirm, mock_prompt, tmp_path
    ):
        """Test interactive initialization with new .env file."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "Test Company",  # denominazione
            "12345678901",  # partita_iva (valid)
            "RSSMRA80A01H501U",  # codice_fiscale (valid)
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "test@pec.it",  # pec_address
            TEST_PEC_PASSWORD,  # pec_password
            "smtp.pec.aruba.it",  # pec_smtp
        ]

        # Change to tmp_path for test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Configuriamo i dati della tua azienda" in result.stdout
            assert "Configurazione salvata" in result.stdout

            # Verify .env file was created
            env_file = tmp_path / ".env"
            assert env_file.exists()

            written_content = env_file.read_text()

            # Check key content in .env
            assert "Test Company" in written_content
            assert "12345678901" in written_content
            assert "RSSMRA80A01H501U" in written_content
            assert "test@pec.it" in written_content
        finally:
            os.chdir(original_cwd)

    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_existing_profile_no_overwrite(
        self, mock_settings, mock_init_db, mock_confirm, tmp_path
    ):
        """Test interactive initialization with existing user profile - user declines overwrite."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # User declines to overwrite
        mock_confirm.ask.return_value = False

        # Create existing user profile file
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            env_file = tmp_path / "profile" / "config.toml"
            env_file.parent.mkdir(parents=True, exist_ok=True)
            env_file.write_text("# Existing content")

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Configurazione esistente mantenuta" in result.stdout
            # Verify original content preserved
            assert "# Existing content" in env_file.read_text()
        finally:
            os.chdir(original_cwd)

    @pytest.mark.skip(
        reason="Complex interactive test - requires working directory mocking refactor"
    )
    @patch("openfatture.cli.commands.init.Prompt")
    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_existing_env_overwrite(
        self, mock_settings, mock_init_db, mock_confirm, mock_prompt, tmp_path
    ):
        """Test interactive initialization with existing .env - user accepts overwrite."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # User accepts overwrite
        mock_confirm.ask.return_value = True

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "Test Company",  # denominazione
            "12345678901",  # partita_iva
            "RSSMRA80A01H501U",  # codice_fiscale
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "test@pec.it",  # pec_address
            TEST_PEC_PASSWORD,  # pec_password
            "smtp.pec.aruba.it",  # pec_smtp
        ]

        # Create existing .env file
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            env_file = tmp_path / ".env"
            env_file.write_text("# Old content")

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Configurazione salvata" in result.stdout
            # Verify file was overwritten
            content = env_file.read_text()
            assert "Test Company" in content
            assert "# Old content" not in content
        finally:
            os.chdir(original_cwd)

    @pytest.mark.skip(
        reason="Complex interactive test - requires working directory mocking refactor"
    )
    @patch("openfatture.cli.commands.init.Prompt")
    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_invalid_partita_iva_then_valid(
        self, mock_settings, mock_init_db, mock_confirm, mock_prompt, tmp_path
    ):
        """Test interactive initialization with invalid then valid Partita IVA."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # Mock user inputs - first P.IVA invalid, then valid
        mock_prompt.ask.side_effect = [
            "Test Company",  # denominazione
            "123",  # partita_iva (INVALID - too short)
            "12345678901",  # partita_iva (valid)
            "RSSMRA80A01H501U",  # codice_fiscale (valid)
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "test@pec.it",  # pec_address
            TEST_PEC_PASSWORD,  # pec_password
            "smtp.pec.aruba.it",  # pec_smtp
        ]

        # Change to tmp_path for test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Partita IVA non valida" in result.stdout
            assert "Configurazione salvata" in result.stdout

            # Verify valid P.IVA was saved
            env_file = tmp_path / ".env"
            content = env_file.read_text()
            assert "12345678901" in content
        finally:
            os.chdir(original_cwd)

    @pytest.mark.skip(
        reason="Complex interactive test - requires working directory mocking refactor"
    )
    @patch("openfatture.cli.commands.init.Prompt")
    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_invalid_codice_fiscale_then_valid(
        self, mock_settings, mock_init_db, mock_confirm, mock_prompt, tmp_path
    ):
        """Test interactive initialization with invalid then valid Codice Fiscale."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # Mock user inputs - first CF invalid, then valid
        mock_prompt.ask.side_effect = [
            "Test Company",  # denominazione
            "12345678901",  # partita_iva (valid)
            "INVALID",  # codice_fiscale (INVALID - too short)
            "RSSMRA80A01H501U",  # codice_fiscale (valid)
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "test@pec.it",  # pec_address
            TEST_PEC_PASSWORD,  # pec_password
            "smtp.pec.aruba.it",  # pec_smtp
        ]

        # Change to tmp_path for test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Codice fiscale non valido" in result.stdout
            assert "Configurazione salvata" in result.stdout

            # Verify valid CF was saved
            env_file = tmp_path / ".env"
            content = env_file.read_text()
            assert "RSSMRA80A01H501U" in content
        finally:
            os.chdir(original_cwd)

    @pytest.mark.skip(
        reason="Complex interactive test - requires working directory mocking refactor"
    )
    @patch("openfatture.cli.commands.init.Prompt")
    @patch("openfatture.cli.commands.init.Confirm")
    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_interactive_with_example_env(
        self, mock_settings, mock_init_db, mock_confirm, mock_prompt, tmp_path
    ):
        """Test interactive initialization when .env.example exists."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        # Mock user inputs
        mock_prompt.ask.side_effect = [
            "Test Company",  # denominazione
            "12345678901",  # partita_iva
            "RSSMRA80A01H501U",  # codice_fiscale
            "Via Roma 1",  # indirizzo
            "00100",  # cap
            "Roma",  # comune
            "RM",  # provincia
            "test@pec.it",  # pec_address
            TEST_PEC_PASSWORD,  # pec_password
            "smtp.pec.aruba.it",  # pec_smtp
        ]

        # Create .env.example
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            example_file = tmp_path / ".env.example"
            example_file.write_text("# Example env content")

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Configurazione salvata" in result.stdout

            # Verify .env was created (not example)
            env_file = tmp_path / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "Test Company" in content
        finally:
            os.chdir(original_cwd)

    @patch("openfatture.cli.commands.init.init_db")
    @patch("openfatture.cli.commands.init.get_settings")
    def test_init_creates_all_directories(self, mock_settings, mock_init_db, tmp_path):
        """Test that all required directories are created."""
        # Setup settings mock
        mock_data_dir = Mock()
        mock_archivio_dir = Mock()
        mock_certificates_dir = Mock()

        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = mock_data_dir
        mock_settings_instance.archivio_dir = mock_archivio_dir
        mock_settings_instance.certificates_dir = mock_certificates_dir
        mock_settings_instance.database_url = f"sqlite:///{tmp_path / 'test.db'}"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["--no-interactive"])

        assert result.exit_code == 0
        # Verify all directories had mkdir called
        mock_data_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_archivio_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_certificates_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_wizard_saves_user_profile_without_assuming_regime(monkeypatch, tmp_path):
    import os
    from types import SimpleNamespace

    import tomlkit

    from openfatture.cli.commands import init
    from openfatture.i18n import _

    profile = tmp_path / "config.toml"
    profile.write_text(
        'ai_api_key = "synthetic-existing-key"\npec_password = "synthetic-existing-password"\n'
    )
    settings = SimpleNamespace(
        data_dir=tmp_path / "data",
        archivio_dir=tmp_path / "archive",
        certificates_dir=tmp_path / "certs",
        database_url=f"sqlite:///{tmp_path}/test.db",
        cedente_regime_fiscale="",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(init, "get_settings", lambda: settings)
    monkeypatch.setattr(init, "init_db", lambda url: None)

    def prompt(label, **kwargs):
        answers = {
            _("cli-init-prompt-name"): "Test",
            _("cli-init-prompt-partita-iva"): "12345678903",
            _("cli-init-prompt-codice-fiscale"): "RSSMRA80A01H501U",
            _("cli-init-prompt-regime"): "RF01",
            _("cli-init-prompt-address"): "Via Roma 1",
            _("cli-init-prompt-cap"): "00100",
            _("cli-init-prompt-city"): "Roma",
            _("cli-init-prompt-province"): "RM",
            _("cli-init-prompt-pec-address"): "test@example.it",
            _("cli-init-prompt-pec-password"): "",
            _("cli-init-prompt-pec-smtp"): "smtp.example.it",
            _("cli-init-prompt-notification-email"): "test@example.it",
            _("cli-init-prompt-locale"): "it",
        }
        return answers[label]

    monkeypatch.setattr(init.Prompt, "ask", prompt)
    monkeypatch.setattr(
        init.Confirm, "ask", lambda label, **kwargs: label == _("cli-init-overwrite-confirm")
    )
    result = runner.invoke(app, [])
    assert result.exit_code == 0, result.output
    saved = tomlkit.parse(profile.read_text())
    assert saved["cedente_regime_fiscale"] == "RF01"
    assert saved["ai_api_key"] == "synthetic-existing-key"
    assert saved["pec_password"] == "synthetic-existing-password"
    assert not (tmp_path / ".env").exists()
    assert os.stat(profile).st_mode & 0o777 == 0o600


def _wizard_settings(tmp_path):
    from types import SimpleNamespace

    return SimpleNamespace(
        data_dir=tmp_path / "data",
        archivio_dir=tmp_path / "archive",
        certificates_dir=tmp_path / "certs",
        database_url=f"sqlite:///{tmp_path}/test.db",
        cedente_regime_fiscale="",
    )


def test_schema_error_aborts_init(monkeypatch, tmp_path):
    from openfatture.cli.commands import init
    from openfatture.storage import schema

    def broken(url):
        raise schema.SchemaError("schema is unusable")

    monkeypatch.setattr(init, "get_settings", lambda: _wizard_settings(tmp_path))
    monkeypatch.setattr(schema, "upgrade_database", broken)
    result = runner.invoke(app, ["--no-interactive"])
    assert result.exit_code == 1
    assert "schema is unusable" in result.output


def test_backup_path_is_reported(monkeypatch, tmp_path):
    from openfatture.cli.commands import init
    from openfatture.storage import schema

    monkeypatch.setattr(init, "get_settings", lambda: _wizard_settings(tmp_path))
    monkeypatch.setattr(init, "init_db", lambda url: None)
    monkeypatch.setattr(schema, "upgrade_database", lambda url: ("legacy", tmp_path / "bak.db"))
    result = runner.invoke(app, ["--no-interactive"])
    assert result.exit_code == 0, result.output
    assert "bak.db" in result.output


AI_PROVIDERS = {"anthropic", "openai", "ollama"}


@pytest.mark.parametrize(
    ("provider", "backends", "hint", "backend_text"),
    [
        ("anthropic", ["keyring", "keyring"], "console.anthropic.com", "portachiavi"),
        ("openai", ["file", "keyring"], "platform.openai.com", "file privato"),
        ("ollama", ["keyring"], "ollama serve", "portachiavi"),
        ("skip", ["file"], None, "file privato"),
        (None, ["file"], None, "file privato"),
    ],
)
def test_wizard_retries_and_configures_ai(
    monkeypatch, tmp_path, provider, backends, hint, backend_text
):
    import tomlkit

    from openfatture.cli import config_file
    from openfatture.cli.commands import init
    from openfatture.i18n import _

    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path / "fresh"))
    monkeypatch.setattr(init, "get_settings", lambda: _wizard_settings(tmp_path))
    monkeypatch.setattr(init, "init_db", lambda url: None)
    answers = {
        _("cli-init-prompt-name"): ["Test"],
        _("cli-init-prompt-partita-iva"): ["123", "12345678903"],
        _("cli-init-prompt-codice-fiscale"): ["BAD", "rssmra80a01h501u"],
        _("cli-init-prompt-regime"): ["rf99", "rf01"],
        _("cli-init-prompt-address"): ["Via Roma 1"],
        _("cli-init-prompt-cap"): ["00100"],
        _("cli-init-prompt-city"): ["Roma"],
        _("cli-init-prompt-province"): ["rm"],
        _("cli-init-prompt-pec-address"): ["test@example.it"],
        _("cli-init-prompt-pec-password"): ["synthetic-pec"],
        _("cli-init-prompt-pec-smtp"): ["smtp.example.it"],
        _("cli-init-prompt-notification-email"): ["test@example.it"],
        _("cli-init-prompt-locale"): ["it"],
        _("cli-init-prompt-api-key"): ["synthetic-ai-key"],
    }

    def prompt(label, **kwargs):
        queue = answers[label]
        return queue.pop(0) if len(queue) > 1 else queue[0]

    monkeypatch.setattr(init.Prompt, "ask", prompt)
    monkeypatch.setattr(
        init.Confirm, "ask", lambda label, **kwargs: label == _("cli-init-ai-confirm")
    )
    choice = _("cli-init-ai-skip") if provider == "skip" else provider
    monkeypatch.setattr(
        init.questionary, "select", lambda *a, **k: Mock(ask=Mock(return_value=choice))
    )
    stored: list[str] = []

    def store(name, value):
        stored.append(name)
        return backends[len(stored) - 1]

    monkeypatch.setattr(config_file, "store_secret", store)

    result = runner.invoke(app, [])

    assert result.exit_code == 0, result.output
    assert "Partita IVA non valida" in result.output
    assert "Codice fiscale non valido" in result.output
    assert "regime fiscale supportato" in result.output
    if hint:
        assert hint in result.output
    assert backend_text in result.output
    saved = tomlkit.parse((tmp_path / "fresh" / "config.toml").read_text())
    assert saved["cedente_partita_iva"] == "12345678903"
    assert saved["cedente_codice_fiscale"] == "RSSMRA80A01H501U"
    assert saved["cedente_regime_fiscale"] == "RF01"
    assert saved["cedente_provincia"] == "RM"
    assert saved.get("ai_provider") == (provider if provider in AI_PROVIDERS else None)
    assert ("ai_base_url" in saved) == (provider == "ollama")
    assert "synthetic" not in (tmp_path / "fresh" / "config.toml").read_text()
    expected = ["pec_password"] + (["ai_api_key"] if provider in {"anthropic", "openai"} else [])
    assert stored == expected


def test_wizard_without_secrets_reports_none(monkeypatch, tmp_path):
    from openfatture.cli import config_file
    from openfatture.cli.commands import init
    from openfatture.i18n import _

    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path / "fresh"))
    monkeypatch.setattr(init, "get_settings", lambda: _wizard_settings(tmp_path))
    monkeypatch.setattr(init, "init_db", lambda url: None)
    defaults = {
        _("cli-init-prompt-partita-iva"): "12345678903",
        _("cli-init-prompt-codice-fiscale"): "RSSMRA80A01H501U",
        _("cli-init-prompt-regime"): "RF01",
    }
    monkeypatch.setattr(init.Prompt, "ask", lambda label, **kwargs: defaults.get(label, ""))
    monkeypatch.setattr(init.Confirm, "ask", lambda label, **kwargs: False)
    monkeypatch.setattr(config_file, "store_secret", Mock(side_effect=AssertionError))
    result = runner.invoke(app, [])
    assert result.exit_code == 0, result.output
    assert "Segreti salvati" not in result.output
