"""ASCII TAB rendering."""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.schema import DecodedTabEvent


_STRING_LABELS = {
    1: "e",
    2: "B",
    3: "G",
    4: "D",
    5: "A",
    6: "E",
}


def render_ascii_tab(events: Sequence[DecodedTabEvent]) -> str:
    """Render positioned events as a simple six-line ASCII TAB."""

    positioned_events = sorted(events, key=lambda event: event.start)
    columns = [
        (
            event.string,
            str(event.fret),
            max(2, len(str(event.fret))),
        )
        for event in positioned_events
    ]

    lines: list[str] = []
    for string_number in range(1, 7):
        body = ""
        for index, (event_string, token, width) in enumerate(columns):
            body += token.ljust(width, "-") if event_string == string_number else "-" * width
            if index < len(columns) - 1:
                body += "-"
        lines.append(f"{_STRING_LABELS[string_number]}|{body}")

    return "\n".join(lines)
