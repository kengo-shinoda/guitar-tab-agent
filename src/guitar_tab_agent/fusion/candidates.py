"""Pitch-to-string/fret candidate generation.

The default tuning is six-string standard tuning from high to low string:

- string 1: E4, MIDI 64
- string 2: B3, MIDI 59
- string 3: G3, MIDI 55
- string 4: D3, MIDI 50
- string 5: A2, MIDI 45
- string 6: E2, MIDI 40
"""

from __future__ import annotations

from guitar_tab_agent.schema import STANDARD_TUNING_MIDI, StringFretCandidate


DEFAULT_MAX_FRET = 24


def candidate_positions_for_midi(
    midi_pitch: int,
    *,
    max_fret: int = DEFAULT_MAX_FRET,
) -> tuple[StringFretCandidate, ...]:
    """Return all standard-tuning positions that can play a MIDI pitch."""

    if not 0 <= midi_pitch <= 127:
        raise ValueError("midi_pitch must be in the MIDI range 0..127")
    if max_fret < 0:
        raise ValueError("max_fret must be non-negative")

    positions: list[StringFretCandidate] = []
    for string_number, open_pitch in sorted(STANDARD_TUNING_MIDI.items()):
        fret_number = midi_pitch - open_pitch
        if 0 <= fret_number <= max_fret:
            positions.append(
                StringFretCandidate(
                    string=string_number,
                    fret=fret_number,
                    pitch_midi=midi_pitch,
                )
            )
    return tuple(positions)
