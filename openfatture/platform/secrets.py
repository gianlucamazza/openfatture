"""Credential storage outside the plain configuration file.

Secrets live in the operating-system keychain through :mod:`keyring` (Secret
Service on Linux, Keychain on macOS, Credential Locker on Windows). When no
usable keychain exists (headless hosts, containers) they are kept in
``credentials.toml`` next to ``config.toml``, readable only by the owner.
``OPENFATTURE_SECRET_BACKEND=keyring|file`` forces a backend.
"""

from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path
from typing import Final, Literal, cast

SECRET_FIELDS: Final[tuple[str, ...]] = (
    "ai_api_key",
    "pec_password",
    "signature_certificate_password",
)
SERVICE: Final = "openfatture"
BACKEND_ENV: Final = "OPENFATTURE_SECRET_BACKEND"
CONFIG_DIR_ENV: Final = "OPENFATTURE_CONFIG_DIR"

BackendName = Literal["keyring", "file"]


def config_dir() -> Path:
    """Directory holding ``config.toml`` and ``credentials.toml``."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    from openfatture.platform.config import dirs

    return Path(dirs.user_config_dir)


def config_file_path() -> Path:
    return config_dir() / "config.toml"


def credentials_file_path() -> Path:
    return config_dir() / "credentials.toml"


def write_private_text(path: Path, text: str) -> None:
    """Atomically write ``text`` to ``path`` with owner-only permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _keyring_usable() -> bool:
    try:
        import keyring
        from keyring.backends import fail
    except ImportError:
        return False
    backend = keyring.get_keyring()
    return not isinstance(backend, fail.Keyring) and getattr(backend, "priority", 0) > 0


def backend_name() -> BackendName:
    forced = os.environ.get(BACKEND_ENV, "").strip().lower()
    if forced == "keyring" or forced == "file":
        return cast(BackendName, forced)
    return "keyring" if _keyring_usable() else "file"


class SecretStore:
    """Read and write the secret settings in the selected backend."""

    def __init__(self, backend: BackendName | None = None) -> None:
        self.backend: BackendName = backend or backend_name()

    def _check(self, name: str) -> None:
        if name not in SECRET_FIELDS:
            raise KeyError(f"{name} is not a secret setting")

    def _read_file(self) -> dict[str, str]:
        path = credentials_file_path()
        if not path.exists():
            return {}
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return {key: str(value) for key, value in data.items() if key in SECRET_FIELDS}

    def _write_file(self, values: dict[str, str]) -> None:
        import tomlkit

        write_private_text(credentials_file_path(), tomlkit.dumps(dict(sorted(values.items()))))

    def get(self, name: str) -> str | None:
        self._check(name)
        if self.backend == "file":
            return self._read_file().get(name)
        import keyring

        return keyring.get_password(SERVICE, name)

    def set(self, name: str, value: str) -> None:
        self._check(name)
        if self.backend == "file":
            values = self._read_file()
            values[name] = value
            self._write_file(values)
            return
        import keyring

        keyring.set_password(SERVICE, name, value)

    def delete(self, name: str) -> bool:
        """Remove ``name``; return False when it was not stored."""
        self._check(name)
        if self.backend == "file":
            values = self._read_file()
            if name not in values:
                return False
            del values[name]
            self._write_file(values)
            return True
        import keyring
        from keyring.errors import PasswordDeleteError

        try:
            keyring.delete_password(SERVICE, name)
        except PasswordDeleteError:
            return False
        return True

    def values(self) -> dict[str, str]:
        """All stored secrets."""
        result: dict[str, str] = {}
        for name in SECRET_FIELDS:
            value = self.get(name)
            if value:
                result[name] = value
        return result
