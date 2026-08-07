"""Stub file for plotly.graph_objects module.

Minimal type hints for plotly.graph_objects classes used in the project.
"""

from collections.abc import Sequence
from typing import Any

class Figure:
    def add_trace(self, trace: Any) -> None: ...
    def update_layout(self, **kwargs: Any) -> None: ...
    def __init__(self, **kwargs: Any) -> None: ...

class Bar:
    def __init__(
        self,
        x: Sequence[Any] | None = None,
        y: Sequence[Any] | None = None,
        marker_color: str | None = None,
        text: Sequence[Any] | None = None,
        textposition: str | None = None,
        **kwargs: Any,
    ) -> None: ...
