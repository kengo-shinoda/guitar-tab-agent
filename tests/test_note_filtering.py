import pytest

from guitar_tab_agent.audio.note_filtering import (
    filter_note_events,
    sort_note_events_chronologically,
    validate_note_filter_thresholds,
)
from guitar_tab_agent.schema import NoteEvent


def note(
    start: float,
    end: float,
    pitch_midi: int,
    confidence: float = 1.0,
) -> NoteEvent:
    return NoteEvent(
        start=start,
        end=end,
        pitch_midi=pitch_midi,
        confidence=confidence,
        source="test",
    )


def test_defaults_preserve_all_notes_in_order() -> None:
    notes = [
        note(0.5, 0.75, 64, 0.2),
        note(0.0, 0.25, 40, 0.9),
    ]

    assert filter_note_events(notes) == notes


def test_sort_note_events_chronologically_uses_stable_tie_breaks() -> None:
    notes = [
        note(1.0, 1.25, 64),
        note(0.5, 0.75, 67),
        note(0.5, 0.70, 69),
        note(0.5, 0.70, 65),
    ]

    assert sort_note_events_chronologically(notes) == [
        notes[3],
        notes[2],
        notes[1],
        notes[0],
    ]


def test_filters_by_min_confidence() -> None:
    notes = [
        note(0.0, 0.25, 64, 0.54),
        note(0.5, 0.75, 65, 0.55),
    ]

    assert filter_note_events(notes, min_confidence=0.55) == [notes[1]]


def test_filters_confidence_none_when_min_confidence_is_set() -> None:
    notes = [note(0.0, 0.25, 64, 0.9)]
    object.__setattr__(notes[0], "confidence", None)

    assert filter_note_events(notes, min_confidence=0.55) == []


def test_filters_by_min_duration() -> None:
    notes = [
        note(0.0, 0.05, 64),
        note(0.5, 0.75, 65),
    ]

    assert filter_note_events(notes, min_duration=0.1) == [notes[1]]


def test_filters_by_inclusive_pitch_bounds() -> None:
    notes = [
        note(0.0, 0.25, 39),
        note(0.5, 0.75, 40),
        note(1.0, 1.25, 88),
        note(1.5, 1.75, 89),
    ]

    assert filter_note_events(notes, min_pitch=40, max_pitch=88) == [
        notes[1],
        notes[2],
    ]


def test_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValueError, match="min_confidence"):
        validate_note_filter_thresholds(min_confidence=1.1)
    with pytest.raises(ValueError, match="min_duration"):
        validate_note_filter_thresholds(min_duration=-0.1)
    with pytest.raises(ValueError, match="min_pitch"):
        validate_note_filter_thresholds(min_pitch=89, max_pitch=88)
