from unittest.mock import patch

from openfatture.platform.config import Settings, reload_settings


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


def test_platformdirs_usage(monkeypatch):
    """Test that platformdirs is actually being used."""
    for name in ("DATA_DIR", "ARCHIVIO_DIR", "CERTIFICATES_DIR", "VECTOR_STORE_PATH"):
        monkeypatch.delenv(name, raising=False)
    import importlib
    from unittest.mock import MagicMock

    import openfatture.platform.config

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
        importlib.reload(openfatture.platform.config)

        MockPlatformDirs.assert_called_once_with("openfatture", "venerelabs")

        settings = openfatture.platform.config.Settings()

        assert str(settings.data_dir) == "/tmp/mock/data"
        assert str(settings.certificates_dir) == "/tmp/mock/config/certificates"
        assert str(settings.debug_config.log_file_path) == "/tmp/mock/log/debug.log"

    # Restore original module state to avoid affecting other tests
    importlib.reload(openfatture.platform.config)


def test_profile_precedence_and_read_only_paths(tmp_path, monkeypatch):
    """explicit > environment > secret store > config.toml > default; ./.env is ignored."""
    import tomlkit

    import openfatture.platform.config as module
    from openfatture.platform.secrets import SecretStore

    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "config.toml").write_text(
        tomlkit.dumps({"cedente_denominazione": "Profile", "pec_password": "toml-secret"})
    )
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(profile))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("CEDENTE_DENOMINAZIONE=Dotenv\nAI_PROVIDER=ollama\n")
    for name in ("CEDENTE_DENOMINAZIONE", "PEC_PASSWORD", "AI_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    paths = {
        "data_dir": tmp_path / "data",
        "archivio_dir": tmp_path / "archive",
        "certificates_dir": tmp_path / "certificates",
    }

    settings = module.Settings(**paths)
    assert settings.cedente_denominazione == "Profile"
    assert settings.ai_provider == module.Settings.model_fields["ai_provider"].default
    assert settings.pec_password == "toml-secret"

    SecretStore().set("pec_password", "store-secret")
    assert module.Settings(**paths).pec_password == "store-secret"

    monkeypatch.setenv("CEDENTE_DENOMINAZIONE", "Environment")
    monkeypatch.setenv("PEC_PASSWORD", "env-secret")
    settings = module.Settings(**paths)
    assert settings.cedente_denominazione == "Environment"
    assert settings.pec_password == "env-secret"
    assert (
        module.Settings(cedente_denominazione="Explicit", **paths).cedente_denominazione
        == "Explicit"
    )

    sources = module.config_sources()
    assert sources["cedente_denominazione"] == "env"
    assert sources["ai_provider"] == "default"
    assert module.plaintext_secrets() == ["pec_password"]
    assert all(not path.exists() for path in paths.values())
