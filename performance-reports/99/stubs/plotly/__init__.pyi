"""Stub file for plotly package.

Minimal type hints for plotly to satisfy mypy type checking.
"""

from typing import Any

__version__: str

def __getattr__(name: str) -> Any: ...
