"""ASCII TAB rendering."""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.models import TabEvent


_STRING_LABELS = {
    1: "e",
    2: "B",
    3: "G",
    4: "D",
    5: "A",
    6: "E",
}


def render_ascii_tab(events: Sequence[TabEvent]) -> str:
    """Render positioned events as a simple six-line ASCII TAB."""

    positioned_events = sorted(
        (event for event in events if event.position is not None),
        key=lambda event: event.note.onset,
    )
    columns = [
        (
            event.position.string_number,
            str(event.position.fret_number),
            max(2, len(str(event.position.fret_number))),
        )
        for event in positioned_events
        if event.position is not None
    ]

    lines: list[str] = []
    for string_number in range(1, 7):
        body = ""
        for event_string, token, width in columns:
            body += token.ljust(width, "-") if event_string == string_number else "-" * width
            body += "-"
        lines.append(f"{_STRING_LABELS[string_number]}|{body}")

    return "\n".join(lines)
