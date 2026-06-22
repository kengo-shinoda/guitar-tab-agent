"""Simple deterministic audio-only TAB decoder.

This is a baseline decoder, not final multimodal decoding. It intentionally
uses a small explicit cost function so behavior is inspectable and stable.
"""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi
from guitar_tab_agent.schema import DecodedTabEvent, NoteEvent, StringFretCandidate


STRING_MOVEMENT_COST_WEIGHT = 0.25

CandidateCost = tuple[float, int, int]


def _candidate_cost(
    candidate: StringFretCandidate,
    previous: DecodedTabEvent | None,
) -> CandidateCost:
    """Return an explicit deterministic cost tuple for a candidate.

    For the first note, the primary cost mildly prefers lower frets while still
    allowing open strings.

    For later notes, the primary cost prefers smaller fret movement from the
    previous decoded note and adds a small string movement cost. Ties then use
    lower fret followed by lower string number. This tie-break is deterministic
    and should not be interpreted as musical preference beyond this baseline.
    """

    if previous is None:
        primary_cost = candidate.fret
    else:
        primary_cost = abs(candidate.fret - previous.fret) + (
            STRING_MOVEMENT_COST_WEIGHT * abs(candidate.string - previous.string)
        )
    return (primary_cost, candidate.fret, candidate.string)


def _confidence_for_cost(cost: CandidateCost) -> float:
    """Map a deterministic baseline cost to a conservative confidence."""

    return max(0.0, min(1.0, 1.0 / (1.0 + cost[0])))


def decode_audio_notes(notes: Sequence[NoteEvent]) -> list[DecodedTabEvent]:
    """Decode monophonic note events into one TAB position per note.

    Notes without any playable standard-tuning candidate are skipped. Polyphony,
    Viterbi/beam search, video evidence, and right-hand evidence are outside
    this baseline.
    """

    decoded: list[DecodedTabEvent] = []
    for note in notes:
        candidates = candidate_positions_for_midi(note.pitch_midi)
        if not candidates:
            continue

        previous = decoded[-1] if decoded else None
        selected = min(
            candidates,
            key=lambda candidate: _candidate_cost(candidate, previous),
        )
        selected_cost = _candidate_cost(selected, previous)
        decoded.append(
            DecodedTabEvent(
                start=note.start,
                end=note.end,
                string=selected.string,
                fret=selected.fret,
                pitch_midi=note.pitch_midi,
                confidence=min(note.confidence, _confidence_for_cost(selected_cost)),
            )
        )

    return decoded


__all__ = [
    "STRING_MOVEMENT_COST_WEIGHT",
    "decode_audio_notes",
]
