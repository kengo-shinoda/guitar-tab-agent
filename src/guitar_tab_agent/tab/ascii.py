"""Backward-compatible ASCII TAB imports.

New code should import from `guitar_tab_agent.tab.ascii_tab`.
"""

from __future__ import annotations

from guitar_tab_agent.tab.ascii_tab import (
    DEFAULT_SECONDS_PER_COLUMN,
    STRING_LABELS,
    render_ascii_tab,
)


__all__ = [
    "DEFAULT_SECONDS_PER_COLUMN",
    "STRING_LABELS",
    "render_ascii_tab",
]
