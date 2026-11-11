"""CLI integration without fixtures that pre-initialize the database."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "command, expected",
    [("fattura", "Nessuna fattura trovata"), ("cliente", "Nessun cliente trovato")],
)
def test_list_initializes_database_in_fresh_process(tmp_path, command, expected):
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ,
        PYTHONPATH=str(root),
        DATABASE_URL=f"sqlite:///{tmp_path}/test.db",
        DATA_DIR=str(tmp_path / "data"),
        ARCHIVIO_DIR=str(tmp_path / "archive"),
        CERTIFICATES_DIR=str(tmp_path / "certs"),
        LOCALE="it",
    )
    result = subprocess.run(
        [sys.executable, "-m", "openfatture.cli.main", command, "list"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout
    assert "Traceback" not in result.stderr


def test_list_database_failure_is_concise(tmp_path):
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ,
        PYTHONPATH=str(root),
        DATABASE_URL=f"sqlite:///{tmp_path}/missing/test.db",
        LOCALE="it",
    )
    result = subprocess.run(
        [sys.executable, "-m", "openfatture.cli.main", "fattura", "list"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "Database non accessibile" in result.stderr
    assert "Traceback" not in result.stdout + result.stderr
