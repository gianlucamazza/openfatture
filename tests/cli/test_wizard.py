import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from openfatture.cli.main import app
from openfatture.utils.config import Settings

runner = CliRunner()


def test_wizard_trigger_on_missing_config():
    """Test that wizard is triggered when config is missing."""
    # Patch dirs where it is imported in main.py
    # Since it is imported inside the function, we might need to patch openfatture.utils.config.dirs
    with (
        patch("openfatture.utils.config.dirs") as mock_dirs,
        patch("openfatture.cli.wizard.run_setup_wizard") as mock_wizard,
        patch("openfatture.cli.main.is_interactive", return_value=True),
    ):

        mock_dirs.user_config_dir = Path("/tmp/mock/config")
        # Ensure config doesn't exist
        # We need to mock the exists() call on the path returned by user_config_dir / "config.toml"
        # But Path objects are hard to mock if we use real Path.
        # Let's rely on the fact that /tmp/mock/config probably doesn't exist or we can ensure it.
        if (mock_dirs.user_config_dir / "config.toml").exists():
            os.remove(mock_dirs.user_config_dir / "config.toml")

        # Actually, since we are patching dirs, we can control what user_config_dir returns.
        # If we return a real path that doesn't exist, it should work.

        # Run app with a subcommand to ensure main callback runs
        # --help might bypass callback if eager
        result = runner.invoke(app, ["config"])
        print(result.stdout)

        mock_wizard.assert_called_once()


def test_save_config():
    """Test saving configuration to TOML."""
    from pathlib import Path

    from openfatture.cli.wizard import save_config

    settings = Settings(cedente_denominazione="Test Corp")
    tmp_path = Path("/tmp/test_config.toml")

    save_config(settings, tmp_path)

    assert tmp_path.exists()
    content = tmp_path.read_text()
    assert "cedente_denominazione" in content
    assert "Test Corp" in content

    # Cleanup
    tmp_path.unlink()
