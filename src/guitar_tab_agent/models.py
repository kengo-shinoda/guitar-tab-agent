"""Backward-compatible model imports.

New code should import canonical dataclasses from `guitar_tab_agent.schema`.
`TabPosition` and `TabEvent` remain as temporary compatibility wrappers for the
initial skeleton API.
"""

from __future__ import annotations

from dataclasses import dataclass

from guitar_tab_agent.schema import (
    STANDARD_TUNING_MIDI,
    DecodedTabEvent,
    FretboardCalibration,
    HandLandmarkFrame,
    NoteEvent,
    StringFretCandidate,
    validate_fret,
    validate_string_number,
)


@dataclass(frozen=True)
class TabPosition:
    """Compatibility wrapper. Prefer `StringFretCandidate` for new code."""

    string_number: int
    fret_number: int

    def __post_init__(self) -> None:
        validate_string_number(self.string_number)
        validate_fret(self.fret_number)

    @property
    def string(self) -> int:
        return self.string_number

    @property
    def fret(self) -> int:
        return self.fret_number

    def to_candidate(
        self,
        *,
        pitch_midi: int,
        confidence: float | None = None,
    ) -> StringFretCandidate:
        return StringFretCandidate(
            string=self.string_number,
            fret=self.fret_number,
            pitch_midi=pitch_midi,
            confidence=confidence,
        )


@dataclass(frozen=True)
class TabEvent:
    """Compatibility wrapper. Prefer `DecodedTabEvent` for new code."""

    note: NoteEvent
    position: TabPosition | StringFretCandidate | None = None


__all__ = [
    "STANDARD_TUNING_MIDI",
    "DecodedTabEvent",
    "FretboardCalibration",
    "HandLandmarkFrame",
    "NoteEvent",
    "StringFretCandidate",
    "TabEvent",
    "TabPosition",
]
