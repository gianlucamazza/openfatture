"""
Tests for PEC CLI commands.
"""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from openfatture.cli.commands.pec import app

runner = CliRunner()
pytestmark = pytest.mark.unit


class TestPECTestCommand:
    """Test 'pec test' command."""

    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_test_no_address(self, mock_settings):
        """Test when PEC address not configured."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = None

        result = runner.invoke(app, ["test"])

        assert result.exit_code == 1
        assert "not configured" in result.stdout

    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_test_no_password(self, mock_settings):
        """Test when PEC password not configured."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_password = None

        result = runner.invoke(app, ["test"])

        assert result.exit_code == 1
        assert "password" in result.stdout.lower()

    @patch("openfatture.cli.commands.pec.PECSender")
    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_test_success(self, mock_settings, mock_sender_class):
        """Test successful PEC test."""
        # Setup settings mock
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_password = "password"
        mock_settings_instance.pec_smtp_server = "smtp.pec.it"
        mock_settings_instance.pec_smtp_port = 465

        # Setup sender mock
        mock_sender = mock_sender_class.return_value
        mock_sender.send_test_email.return_value = (True, None)

        result = runner.invoke(app, ["test"])

        assert result.exit_code == 0
        assert "successfully" in result.stdout.lower()
        mock_sender.send_test_email.assert_called_once()

    @patch("openfatture.cli.commands.pec.PECSender")
    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_test_failure(self, mock_settings, mock_sender_class):
        """Test PEC test failure."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_password = "password"
        mock_settings_instance.pec_smtp_server = "smtp.pec.it"
        mock_settings_instance.pec_smtp_port = 465

        mock_sender = mock_sender_class.return_value
        mock_sender.send_test_email.return_value = (False, "Authentication failed")

        result = runner.invoke(app, ["test"])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()


class TestPECInfoCommand:
    """Test 'pec info' command."""

    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_info_displays_configuration(self, mock_settings):
        """Test that PEC info displays configuration."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = "configured@pec.it"
        mock_settings_instance.pec_password = "secret"
        mock_settings_instance.pec_smtp_server = "smtp.pec.aruba.it"
        mock_settings_instance.pec_smtp_port = 465
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "configured@pec.it" in result.stdout
        assert "smtp.pec.aruba.it" in result.stdout
        assert "465" in result.stdout

    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_info_shows_not_set(self, mock_settings):
        """Test that PEC info shows 'Not set' for missing values."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = None
        mock_settings_instance.pec_password = None
        mock_settings_instance.pec_smtp_server = "smtp.pec.it"
        mock_settings_instance.pec_smtp_port = 465
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "Not set" in result.stdout

    @patch("openfatture.cli.commands.pec.get_settings")
    def test_pec_info_masks_password(self, mock_settings):
        """Test that PEC info doesn't show actual password."""
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.pec_address = "test@pec.it"
        mock_settings_instance.pec_password = "supersecret123"
        mock_settings_instance.pec_smtp_server = "smtp.pec.it"
        mock_settings_instance.pec_smtp_port = 465
        mock_settings_instance.sdi_pec_address = "sdi@pec.fatturapa.it"

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        # Password should be shown as "Set" not the actual value
        assert "supersecret123" not in result.stdout
        assert "Set" in result.stdout or "Not set" in result.stdout
