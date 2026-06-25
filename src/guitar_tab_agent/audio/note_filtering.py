"""Pure-Python filters for normalized NoteEvent records."""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.schema import NoteEvent


def sort_note_events_chronologically(notes: Sequence[NoteEvent]) -> list[NoteEvent]:
    """Return notes sorted by a deterministic chronological key."""

    return sorted(notes, key=lambda note: (note.start, note.end, note.pitch_midi))


def filter_note_events(
    notes: Sequence[NoteEvent],
    *,
    min_confidence: float | None = None,
    min_duration: float | None = None,
    min_pitch: int | None = None,
    max_pitch: int | None = None,
) -> list[NoteEvent]:
    """Return notes that satisfy the provided optional thresholds.

    Defaults preserve behavior exactly: when all thresholds are `None`, all
    input notes are returned in order. Pitch bounds are inclusive.
    """

    validate_note_filter_thresholds(
        min_confidence=min_confidence,
        min_duration=min_duration,
        min_pitch=min_pitch,
        max_pitch=max_pitch,
    )

    filtered: list[NoteEvent] = []
    for note in notes:
        if min_confidence is not None:
            if note.confidence is None or note.confidence < min_confidence:
                continue
        if min_duration is not None and note.end - note.start < min_duration:
            continue
        if min_pitch is not None and note.pitch_midi < min_pitch:
            continue
        if max_pitch is not None and note.pitch_midi > max_pitch:
            continue
        filtered.append(note)

    return filtered


def validate_note_filter_thresholds(
    *,
    min_confidence: float | None = None,
    min_duration: float | None = None,
    min_pitch: int | None = None,
    max_pitch: int | None = None,
) -> None:
    """Validate optional NoteEvent filter thresholds."""

    if min_confidence is not None and not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0.0 and 1.0")
    if min_duration is not None and min_duration < 0:
        raise ValueError("min_duration must be non-negative")
    if min_pitch is not None and max_pitch is not None and min_pitch > max_pitch:
        raise ValueError("min_pitch must be less than or equal to max_pitch")


__all__ = [
    "filter_note_events",
    "sort_note_events_chronologically",
    "validate_note_filter_thresholds",
]
