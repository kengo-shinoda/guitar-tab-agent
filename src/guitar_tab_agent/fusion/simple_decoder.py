"""Simple deterministic TAB decoder.

This is a baseline decoder, not final multimodal decoding. It intentionally
uses a small explicit cost function so behavior is inspectable and stable.

Optional left-hand fret likelihood may be supplied as decoder evidence. When no
left-hand evidence is provided for a note time, behavior matches the audio-only
baseline. Open strings receive neutral left-hand evidence because fret 0 has no
fretting-hand position.

Current limitations: no right-hand evidence, tapping logic, left-handed player
support, temporal smoothing, Viterbi, or beam search.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi
from guitar_tab_agent.schema import DecodedTabEvent, NoteEvent, StringFretCandidate


STRING_MOVEMENT_COST_WEIGHT = 0.25
DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT = 6.0

CandidateCost = tuple[float, int, int]
LeftHandFretLikelihood = Mapping[int, float]
LeftHandFretLikelihoodByTime = Mapping[float, LeftHandFretLikelihood | None]


@dataclass(frozen=True)
class CandidateScoreBreakdown:
    """Inspectable score components for one candidate choice."""

    candidate: StringFretCandidate
    base_cost: float
    left_hand_likelihood: float | None
    left_hand_cost: float
    total_cost: float
    tie_break_fret: int
    tie_break_string: int

    @property
    def cost_tuple(self) -> CandidateCost:
        """Return the deterministic tuple used for candidate ordering."""

        return (self.total_cost, self.tie_break_fret, self.tie_break_string)


@dataclass(frozen=True)
class DecodedNoteDebug:
    """Debug information for one decoded note."""

    note: NoteEvent
    selected: DecodedTabEvent
    candidate_scores: tuple[CandidateScoreBreakdown, ...]


def _candidate_cost(
    candidate: StringFretCandidate,
    previous: DecodedTabEvent | None,
    *,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
) -> CandidateCost:
    """Return an explicit deterministic cost tuple for a candidate.

    For the first note, the primary cost mildly prefers lower frets while still
    allowing open strings.

    For later notes, the primary cost prefers smaller fret movement from the
    previous decoded note and adds a small string movement cost. Ties then use
    lower fret followed by lower string number. This tie-break is deterministic
    and should not be interpreted as musical preference beyond this baseline.
    """

    return _candidate_score_breakdown(
        candidate,
        previous,
        left_hand_fret_likelihood=left_hand_fret_likelihood,
        left_hand_weight=left_hand_weight,
    ).cost_tuple


def _candidate_score_breakdown(
    candidate: StringFretCandidate,
    previous: DecodedTabEvent | None,
    *,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None,
    left_hand_weight: float,
) -> CandidateScoreBreakdown:
    if previous is None:
        base_cost = float(candidate.fret)
    else:
        base_cost = abs(candidate.fret - previous.fret) + (
            STRING_MOVEMENT_COST_WEIGHT * abs(candidate.string - previous.string)
        )

    likelihood = _left_hand_likelihood_for_candidate(
        candidate,
        left_hand_fret_likelihood,
    )
    left_hand_cost = 0.0 if likelihood is None else -(left_hand_weight * likelihood)
    total_cost = base_cost + left_hand_cost
    return CandidateScoreBreakdown(
        candidate=candidate,
        base_cost=base_cost,
        left_hand_likelihood=likelihood,
        left_hand_cost=left_hand_cost,
        total_cost=total_cost,
        tie_break_fret=candidate.fret,
        tie_break_string=candidate.string,
    )


def _left_hand_likelihood_for_candidate(
    candidate: StringFretCandidate,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None,
) -> float | None:
    if left_hand_fret_likelihood is None:
        return None
    if candidate.fret == 0:
        return 0.0
    return max(0.0, float(left_hand_fret_likelihood.get(candidate.fret, 0.0)))


def _confidence_for_cost(cost: CandidateCost) -> float:
    """Map a deterministic baseline cost to a conservative confidence."""

    confidence_cost = max(0.0, cost[0])
    return max(0.0, min(1.0, 1.0 / (1.0 + confidence_cost)))


def decode_audio_notes(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
) -> list[DecodedTabEvent]:
    """Decode monophonic note events into one TAB position per note.

    Notes without any playable standard-tuning candidate are skipped. Polyphony,
    Viterbi/beam search, right-hand evidence, tapping, and left-handed player
    support are outside this baseline. Left-hand fret likelihood is optional
    evidence keyed by note start time; omitting it preserves audio-only behavior.
    """

    debug_events = decode_audio_notes_with_debug(
        notes,
        left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
        left_hand_weight=left_hand_weight,
    )
    return [debug_event.selected for debug_event in debug_events]


def decode_audio_notes_with_debug(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
) -> tuple[DecodedNoteDebug, ...]:
    """Decode notes and return per-candidate score breakdowns.

    `left_hand_weight` controls how strongly a fretted candidate is favored when
    left-hand likelihood is present for the note's start time. The left-hand
    contribution is `-left_hand_weight * likelihood`.
    """

    if left_hand_weight < 0:
        raise ValueError("left_hand_weight must be non-negative")

    decoded: list[DecodedTabEvent] = []
    debug_events: list[DecodedNoteDebug] = []
    for note in notes:
        candidates = candidate_positions_for_midi(note.pitch_midi)
        if not candidates:
            continue

        previous = decoded[-1] if decoded else None
        left_hand_fret_likelihood = _left_hand_likelihood_for_note(
            note,
            left_hand_fret_likelihood_by_time,
        )
        candidate_scores = tuple(
            _candidate_score_breakdown(
                candidate,
                previous,
                left_hand_fret_likelihood=left_hand_fret_likelihood,
                left_hand_weight=left_hand_weight,
            )
            for candidate in candidates
        )
        selected_score = min(candidate_scores, key=lambda score: score.cost_tuple)
        selected = selected_score.candidate
        decoded_event = DecodedTabEvent(
            start=note.start,
            end=note.end,
            string=selected.string,
            fret=selected.fret,
            pitch_midi=note.pitch_midi,
            confidence=min(
                note.confidence,
                _confidence_for_cost(selected_score.cost_tuple),
            ),
        )
        decoded.append(decoded_event)
        debug_events.append(
            DecodedNoteDebug(
                note=note,
                selected=decoded_event,
                candidate_scores=candidate_scores,
            )
        )

    return tuple(debug_events)


def _left_hand_likelihood_for_note(
    note: NoteEvent,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None,
) -> LeftHandFretLikelihood | None:
    if left_hand_fret_likelihood_by_time is None:
        return None
    return left_hand_fret_likelihood_by_time.get(note.start)


__all__ = [
    "CandidateScoreBreakdown",
    "DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT",
    "DecodedNoteDebug",
    "LeftHandFretLikelihood",
    "LeftHandFretLikelihoodByTime",
    "STRING_MOVEMENT_COST_WEIGHT",
    "decode_audio_notes",
    "decode_audio_notes_with_debug",
]
