"""Deterministic six-line ASCII TAB rendering.

This renderer is intentionally simple: it places decoded TAB events into
quantized time slots and prints fret numbers on the matching string. It does
not attempt rhythm-perfect spacing, tied notes, chords, articulations, or
publication-quality notation.
"""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.schema import DecodedTabEvent


STRING_LABELS: dict[int, str] = {
    1: "e",
    2: "B",
    3: "G",
    4: "D",
    5: "A",
    6: "E",
}

DEFAULT_SECONDS_PER_COLUMN = 0.25


def _time_slot(start: float, seconds_per_column: float) -> int:
    return max(0, round(start / seconds_per_column))


def render_ascii_tab(
    events: Sequence[DecodedTabEvent],
    *,
    seconds_per_column: float = DEFAULT_SECONDS_PER_COLUMN,
) -> str:
    """Render decoded events as a stable six-line ASCII TAB draft.

    Events are sorted deterministically, then assigned to time slots using
    `round(event.start / seconds_per_column)`. Each time slot is widened when
    needed to fit two-digit or larger fret numbers.
    """

    if seconds_per_column <= 0:
        raise ValueError("seconds_per_column must be positive")

    sorted_events = sorted(
        events,
        key=lambda event: (
            event.start,
            event.end,
            event.string,
            event.fret,
            event.pitch_midi,
        ),
    )
    if not sorted_events:
        return "\n".join(f"{label}|" for label in STRING_LABELS.values())

    events_by_slot_and_string: dict[tuple[int, int], str] = {}
    slot_widths: dict[int, int] = {}
    for event in sorted_events:
        slot = _time_slot(event.start, seconds_per_column)
        token = str(event.fret)
        key = (slot, event.string)

        # A single monophonic decoded stream should not collide, but this keeps
        # output stable if multiple events quantize onto the same string/slot.
        events_by_slot_and_string.setdefault(key, token)
        slot_widths[slot] = max(slot_widths.get(slot, 1), len(token))

    max_slot = max(slot_widths)
    widths = [slot_widths.get(slot, 1) for slot in range(max_slot + 1)]

    lines: list[str] = []
    for string_number, label in STRING_LABELS.items():
        body_parts: list[str] = []
        for slot, width in enumerate(widths):
            token = events_by_slot_and_string.get((slot, string_number))
            body_parts.append(token.ljust(width, "-") if token else "-" * width)
        lines.append(f"{label}|{''.join(body_parts)}")

    return "\n".join(lines)


__all__ = [
    "DEFAULT_SECONDS_PER_COLUMN",
    "STRING_LABELS",
    "render_ascii_tab",
]
