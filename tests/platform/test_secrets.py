"""Secret storage: OS keychain via keyring, private file fallback."""

import os

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.backends import fail
from keyring.errors import PasswordDeleteError

from openfatture.platform import secrets
from openfatture.platform.secrets import SecretStore, backend_name


class MemoryKeyring(KeyringBackend):
    priority = 10

    def __init__(self) -> None:
        super().__init__()
        self.items: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.items.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.items[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        if self.items.pop((service, username), None) is None:
            raise PasswordDeleteError(username)


@pytest.fixture
def memory_keyring(monkeypatch):
    backend = MemoryKeyring()
    previous = keyring.get_keyring()
    keyring.set_keyring(backend)
    monkeypatch.delenv("OPENFATTURE_SECRET_BACKEND", raising=False)
    yield backend
    keyring.set_keyring(previous)


def test_file_backend_round_trip_is_private(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path))
    store = SecretStore("file")

    store.set("ai_api_key", "sk-one")
    store.set("pec_password", "pw")

    path = tmp_path / "credentials.toml"
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"
    assert store.values() == {"ai_api_key": "sk-one", "pec_password": "pw"}
    assert store.delete("ai_api_key") is True
    assert store.delete("ai_api_key") is False
    assert store.get("ai_api_key") is None
    assert not list(tmp_path.glob(".credentials.toml.*"))  # no leftover temp files


def test_keyring_backend_uses_service_name(memory_keyring):
    assert backend_name() == "keyring"
    store = SecretStore()

    store.set("pec_password", "pw")

    assert memory_keyring.items == {("openfatture", "pec_password"): "pw"}
    assert store.values() == {"pec_password": "pw"}
    assert store.delete("pec_password") is True
    assert store.delete("pec_password") is False


def test_falls_back_to_file_without_usable_keychain(monkeypatch):
    previous = keyring.get_keyring()
    keyring.set_keyring(fail.Keyring())
    monkeypatch.delenv("OPENFATTURE_SECRET_BACKEND", raising=False)
    try:
        assert backend_name() == "file"
    finally:
        keyring.set_keyring(previous)


def test_backend_can_be_forced(memory_keyring, monkeypatch):
    monkeypatch.setenv("OPENFATTURE_SECRET_BACKEND", "file")
    assert backend_name() == "file"


def test_only_secret_fields_are_accepted():
    with pytest.raises(KeyError):
        SecretStore("file").set("ai_model", "x")
    assert "pec_password" in secrets.SECRET_FIELDS
