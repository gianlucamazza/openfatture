"""Stub file for plotly.express module.

Minimal type hints for plotly.express functions used in the project.
"""

from collections.abc import Sequence
from typing import Any

def bar(
    data_frame: Any | None = None,
    x: Any | None = None,
    y: Any | None = None,
    title: str | None = None,
    labels: dict[str, str] | None = None,
    color: Any | None = None,
    color_continuous_scale: str | None = None,
    **kwargs: Any,
) -> Any: ...
def pie(
    values: Sequence[Any] | None = None,
    names: Sequence[Any] | None = None,
    title: str | None = None,
    hole: float | None = None,
    **kwargs: Any,
) -> Any: ...
def line(
    x: Sequence[Any] | None = None,
    y: Sequence[Any] | None = None,
    title: str | None = None,
    labels: dict[str, str] | None = None,
    markers: bool = False,
    **kwargs: Any,
) -> Any: ...

class colors:
    class qualitative:
        Set3: list[str]
