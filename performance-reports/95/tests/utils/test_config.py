from unittest.mock import patch

from openfatture.utils.config import Settings, reload_settings


def test_settings_defaults():
    """Test that default settings use platformdirs."""
    settings = Settings()

    # Check that paths are not in ~/.openfatture (unless mocked)
    # We can't easily check for "platformdirs" without mocking it,
    # but we can check that they are absolute paths.
    assert settings.data_dir.is_absolute()
    assert settings.archivio_dir.is_absolute()
    assert settings.certificates_dir.is_absolute()

    # Check relationship between dirs
    assert settings.archivio_dir == settings.data_dir / "archivio"


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    # Settings does not have a prefix defined, so it matches field names directly (case-insensitive)
    monkeypatch.setenv("CEDENTE_DENOMINAZIONE", "Test Corp")
    monkeypatch.setenv("DEBUG", "true")

    settings = reload_settings()

    assert settings.cedente_denominazione == "Test Corp"
    assert settings.debug is True


def test_platformdirs_usage():
    """Test that platformdirs is actually being used."""
    import importlib
    from unittest.mock import MagicMock

    import openfatture.utils.config

    # We need to patch where PlatformDirs is instantiated or used
    # Since 'dirs' is a global in the module, we can patch the module attribute
    # BUT the class attributes are already evaluated.
    # So we must reload the module while patching PlatformDirs class

    # Patch the library directly to ensure it catches the instantiation during reload
    with patch("platformdirs.PlatformDirs") as MockPlatformDirs:
        mock_instance = MagicMock()
        mock_instance.user_data_dir = "/tmp/mock/data"
        mock_instance.user_config_dir = "/tmp/mock/config"
        mock_instance.user_log_dir = "/tmp/mock/log"
        MockPlatformDirs.return_value = mock_instance

        # Reload the module so the class definitions are re-evaluated with the mock
        importlib.reload(openfatture.utils.config)

        settings = openfatture.utils.config.Settings()

        assert str(settings.data_dir) == "/tmp/mock/data"
        assert str(settings.certificates_dir) == "/tmp/mock/config/certificates"
        assert str(settings.debug_config.log_file_path) == "/tmp/mock/log/debug.log"

    # Restore original module state to avoid affecting other tests
    importlib.reload(openfatture.utils.config)
