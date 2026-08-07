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
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["--no-interactive"])

        assert result.exit_code == 0
        assert "OpenFatture Setup" in result.stdout
        assert "Creating directories" in result.stdout
        assert "Initializing database" in result.stdout
        assert "Setup Complete" in result.stdout

        # Verify init_db was called
        mock_init_db.assert_called_once_with("sqlite:///test.db")

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
        mock_settings_instance.database_url = "sqlite:///test.db"
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
            assert "Let's configure your company data" in result.stdout
            assert "Configuration saved" in result.stdout

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
    def test_init_interactive_existing_env_no_overwrite(
        self, mock_settings, mock_init_db, mock_confirm, tmp_path
    ):
        """Test interactive initialization with existing .env - user declines overwrite."""
        # Setup settings mock
        mock_settings_instance = Mock()
        mock_settings_instance.data_dir = tmp_path / "data"
        mock_settings_instance.archivio_dir = tmp_path / "archivio"
        mock_settings_instance.certificates_dir = tmp_path / "certificates"
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        # User declines to overwrite
        mock_confirm.ask.return_value = False

        # Create existing .env file
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            env_file = tmp_path / ".env"
            env_file.write_text("# Existing content")

            result = runner.invoke(app, ["--interactive"])

            assert result.exit_code == 0
            assert "Existing .env preserved" in result.stdout
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
        mock_settings_instance.database_url = "sqlite:///test.db"
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
            assert "Configuration saved" in result.stdout
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
        mock_settings_instance.database_url = "sqlite:///test.db"
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
            assert "Invalid Partita IVA" in result.stdout
            assert "Configuration saved" in result.stdout

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
        mock_settings_instance.database_url = "sqlite:///test.db"
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
            assert "Invalid Codice Fiscale" in result.stdout
            assert "Configuration saved" in result.stdout

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
        mock_settings_instance.database_url = "sqlite:///test.db"
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
            assert "Configuration saved" in result.stdout

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
        mock_settings_instance.database_url = "sqlite:///test.db"
        mock_settings.return_value = mock_settings_instance

        result = runner.invoke(app, ["--no-interactive"])

        assert result.exit_code == 0
        # Verify all directories had mkdir called
        mock_data_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_archivio_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_certificates_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
