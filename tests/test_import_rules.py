"""Enforce the package import rules documented in docs/ARCHITECTURE.md."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "openfatture"

FORBIDDEN = {
    "billing": ("openfatture.cli", "openfatture.ai"),
    "payment": ("openfatture.cli", "openfatture.ai"),
    "sdi": ("openfatture.cli", "openfatture.ai"),
    "pdf": ("openfatture.cli", "openfatture.ai"),
    "storage": ("openfatture.cli", "openfatture.ai"),
    "events": ("openfatture.cli", "openfatture.ai"),
    "hooks": ("openfatture.cli", "openfatture.ai"),
    "platform": (
        "openfatture.cli",
        "openfatture.ai",
        "openfatture.billing",
        "openfatture.payment",
        "openfatture.sdi",
        "openfatture.pdf",
    ),
    "ai": ("openfatture.cli",),
}


def _imports(path: Path) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.lineno, node.module))
    return found


@pytest.mark.parametrize("package", sorted(FORBIDDEN))
def test_package_does_not_import_upper_layers(package: str) -> None:
    prefixes = FORBIDDEN[package]
    violations = [
        f"{path.relative_to(ROOT.parent)}:{line} imports {module}"
        for path in sorted((ROOT / package).rglob("*.py"))
        for line, module in _imports(path)
        if any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)
    ]
    assert not violations, "\n".join(violations)
