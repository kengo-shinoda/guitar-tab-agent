"""Shared internal models for the TAB generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass


STANDARD_TUNING_MIDI: dict[int, int] = {
    1: 64,
    2: 59,
    3: 55,
    4: 50,
    5: 45,
    6: 40,
}


@dataclass(frozen=True)
class NoteEvent:
    """A normalized note event produced by an audio transcription stage."""

    onset: float
    duration: float
    midi_pitch: int
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.onset < 0:
            raise ValueError("onset must be non-negative")
        if self.duration < 0:
            raise ValueError("duration must be non-negative")
        if not 0 <= self.midi_pitch <= 127:
            raise ValueError("midi_pitch must be in the MIDI range 0..127")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class TabPosition:
    """A guitar string/fret position using standard string numbering."""

    string_number: int
    fret_number: int

    def __post_init__(self) -> None:
        if self.string_number not in STANDARD_TUNING_MIDI:
            raise ValueError("string_number must be between 1 and 6")
        if self.fret_number < 0:
            raise ValueError("fret_number must be non-negative")


@dataclass(frozen=True)
class TabEvent:
    """A note event with an optional selected TAB position."""

    note: NoteEvent
    position: TabPosition | None = None
