"""Pitch-to-position candidate generation."""

from __future__ import annotations

from guitar_tab_agent.models import STANDARD_TUNING_MIDI, TabPosition


def candidate_positions_for_midi(
    midi_pitch: int,
    *,
    max_fret: int = 24,
) -> tuple[TabPosition, ...]:
    """Return all standard-tuning positions that can play a MIDI pitch."""

    if not 0 <= midi_pitch <= 127:
        raise ValueError("midi_pitch must be in the MIDI range 0..127")
    if max_fret < 0:
        raise ValueError("max_fret must be non-negative")

    positions: list[TabPosition] = []
    for string_number, open_pitch in sorted(STANDARD_TUNING_MIDI.items()):
        fret_number = midi_pitch - open_pitch
        if 0 <= fret_number <= max_fret:
            positions.append(
                TabPosition(
                    string_number=string_number,
                    fret_number=fret_number,
                )
            )
    return tuple(positions)
