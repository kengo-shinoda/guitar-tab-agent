"""Deterministic ergonomic TAB decoder.

This is a baseline decoder, not final multimodal decoding. It intentionally
uses a small explicit cost function so behavior is inspectable and stable.

Optional left-hand fret likelihood may be supplied as decoder evidence. When no
left-hand evidence is provided for a note time, behavior matches the audio-only
baseline. Open strings receive neutral left-hand evidence because fret 0 has no
fretting-hand position.

Current limitations: no right-hand evidence, tapping logic, left-handed player
support, or beam search.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi
from guitar_tab_agent.schema import DecodedTabEvent, NoteEvent, StringFretCandidate


INITIAL_FRET_COST_WEIGHT = 1.0
FRET_MOVEMENT_COST_WEIGHT = 1.0
STRING_MOVEMENT_COST_WEIGHT = 0.25
POSITION_SHIFT_COST_WEIGHT = 0.5
POSITION_BOX_SHIFT_COST_WEIGHT = 0.5
REPEATED_NOTE_SWITCH_COST_WEIGHT = 2.0
OPEN_STRING_COST_WEIGHT = 3.0
HIGH_FRET_COST_WEIGHT = 0.05
HIGH_FRET_EXTRA_THRESHOLD = 17
HIGH_FRET_EXTRA_COST_WEIGHT = 0.15
NON_FIRST_STRING_VERY_HIGH_FRET_THRESHOLD = 21
NON_FIRST_STRING_VERY_HIGH_FRET_COST = 3.0
DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT = 6.0

CandidateCost = tuple[float, int, int]
LeftHandFretLikelihood = Mapping[int, float]
LeftHandFretLikelihoodByTime = Mapping[float, LeftHandFretLikelihood | None]
_FINGERING_POSITION_PATTERN = re.compile(r"^(?P<string>[1-6])s-(?P<fret>\d+)f$")


@dataclass(frozen=True)
class FingeringPosition:
    """A user-provided guitar string/fret position hint."""

    string: int
    fret: int

    def __post_init__(self) -> None:
        if not 1 <= self.string <= 6:
            raise ValueError("string must be between 1 and 6")
        if self.fret < 0:
            raise ValueError("fret must be non-negative")


@dataclass(frozen=True)
class ErgonomicDecoderWeights:
    """Tunable non-negative weights for audio-only fingering path search."""

    initial_fret: float = INITIAL_FRET_COST_WEIGHT
    fret_movement: float = FRET_MOVEMENT_COST_WEIGHT
    string_movement: float = STRING_MOVEMENT_COST_WEIGHT
    position_shift: float = POSITION_SHIFT_COST_WEIGHT
    position_box_shift: float = POSITION_BOX_SHIFT_COST_WEIGHT
    repeated_note_switch: float = REPEATED_NOTE_SWITCH_COST_WEIGHT
    open_string: float = OPEN_STRING_COST_WEIGHT
    high_fret: float = HIGH_FRET_COST_WEIGHT

    def __post_init__(self) -> None:
        for name, value in (
            ("initial_fret", self.initial_fret),
            ("fret_movement", self.fret_movement),
            ("string_movement", self.string_movement),
            ("position_shift", self.position_shift),
            ("position_box_shift", self.position_box_shift),
            ("repeated_note_switch", self.repeated_note_switch),
            ("open_string", self.open_string),
            ("high_fret", self.high_fret),
        ):
            if value < 0:
                raise ValueError(f"{name} weight must be non-negative")


def parse_fingering_position(value: str) -> FingeringPosition:
    """Parse compact fingering shorthand such as `5s-0f`."""

    match = _FINGERING_POSITION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            "first_position must use format '<string>s-<fret>f', such as '5s-0f'"
        )
    return FingeringPosition(
        string=int(match.group("string")),
        fret=int(match.group("fret")),
    )


@dataclass(frozen=True)
class CandidateScoreBreakdown:
    """Inspectable score components for one candidate choice."""

    candidate: StringFretCandidate
    base_cost: float
    initial_fret_cost: float
    fret_movement_cost: float
    string_movement_cost: float
    position_shift_cost: float
    candidate_position_box_start: int | None
    previous_position_box_start: int | None
    position_box_shift_cost: float
    repeated_note_switch_cost: float
    open_string_cost: float
    high_fret_cost: float
    left_hand_likelihood: float | None
    left_hand_cost: float
    total_cost: float
    sequence_cost: float
    tie_break_fret: int
    tie_break_string: int
    previous_candidate: StringFretCandidate | None = None

    @property
    def cost_tuple(self) -> CandidateCost:
        """Return the deterministic tuple used for local candidate ordering."""

        return (self.total_cost, self.tie_break_fret, self.tie_break_string)


@dataclass(frozen=True)
class _PathState:
    score: CandidateScoreBreakdown
    previous_index: int | None


@dataclass(frozen=True)
class DecodedNoteDebug:
    """Debug information for one decoded note."""

    note: NoteEvent
    selected: DecodedTabEvent
    candidate_scores: tuple[CandidateScoreBreakdown, ...]


@dataclass(frozen=True)
class DecodedTabCandidate:
    """One ranked decoded TAB candidate path."""

    events: tuple[DecodedTabEvent, ...]
    total_score: float
    rank: int


@dataclass(frozen=True)
class _TopKPathState:
    scores: tuple[CandidateScoreBreakdown, ...]

    @property
    def sequence_cost(self) -> float:
        return self.scores[-1].sequence_cost

    @property
    def candidate(self) -> StringFretCandidate:
        return self.scores[-1].candidate

    @property
    def path_key(self) -> tuple[tuple[int, int], ...]:
        return tuple((score.candidate.string, score.candidate.fret) for score in self.scores)


def _candidate_cost(
    candidate: StringFretCandidate,
    previous: DecodedTabEvent | None,
    *,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    weights: ErgonomicDecoderWeights = ErgonomicDecoderWeights(),
) -> CandidateCost:
    """Return an explicit deterministic local cost tuple for a candidate."""

    return _candidate_score_breakdown(
        candidate,
        previous_candidate=_candidate_from_decoded_event(previous),
        previous_pitch_midi=None,
        previous_sequence_cost=0.0,
        left_hand_fret_likelihood=left_hand_fret_likelihood,
        left_hand_weight=left_hand_weight,
        weights=weights,
    ).cost_tuple


def _candidate_score_breakdown(
    candidate: StringFretCandidate,
    *,
    previous_candidate: StringFretCandidate | None,
    previous_pitch_midi: int | None,
    previous_sequence_cost: float,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None,
    left_hand_weight: float,
    weights: ErgonomicDecoderWeights,
) -> CandidateScoreBreakdown:
    initial_fret_cost = 0.0
    fret_movement_cost = 0.0
    string_movement_cost = 0.0
    position_shift_cost = 0.0
    candidate_position_box_start = _position_box_start(candidate.fret)
    previous_position_box_start = None
    position_box_shift_cost = 0.0
    repeated_note_switch_cost = 0.0
    if previous_candidate is None:
        initial_fret_cost = weights.initial_fret * candidate.fret
    else:
        previous_position_box_start = _position_box_start(previous_candidate.fret)
        fret_delta = abs(candidate.fret - previous_candidate.fret)
        string_delta = abs(candidate.string - previous_candidate.string)
        fret_movement_cost = weights.fret_movement * fret_delta
        string_movement_cost = weights.string_movement * string_delta
        # This mild extra term nudges the selected phrase toward stable hand
        # positions without trying to model full guitar technique.
        position_shift_cost = weights.position_shift * max(0, fret_delta - 4)
        if (
            candidate_position_box_start is not None
            and previous_position_box_start is not None
        ):
            position_box_shift_cost = weights.position_box_shift * abs(
                candidate_position_box_start - previous_position_box_start
            )
        if (
            previous_pitch_midi == candidate.pitch_midi
            and (
                previous_candidate.string != candidate.string
                or previous_candidate.fret != candidate.fret
            )
        ):
            repeated_note_switch_cost = weights.repeated_note_switch

    open_string_cost = (
        weights.open_string
        if candidate.fret == 0
        and previous_candidate is not None
        and (
            previous_candidate.string != candidate.string
            or previous_candidate.fret != candidate.fret
        )
        else 0.0
    )
    high_fret_cost = weights.high_fret * candidate.fret
    if candidate.fret > HIGH_FRET_EXTRA_THRESHOLD:
        high_fret_cost += (
            candidate.fret - HIGH_FRET_EXTRA_THRESHOLD
        ) * HIGH_FRET_EXTRA_COST_WEIGHT
    if (
        candidate.string != 1
        and candidate.fret >= NON_FIRST_STRING_VERY_HIGH_FRET_THRESHOLD
    ):
        high_fret_cost += NON_FIRST_STRING_VERY_HIGH_FRET_COST

    base_cost = (
        initial_fret_cost
        + fret_movement_cost
        + string_movement_cost
        + position_shift_cost
        + position_box_shift_cost
        + repeated_note_switch_cost
        + open_string_cost
        + high_fret_cost
    )

    likelihood = _left_hand_likelihood_for_candidate(
        candidate,
        left_hand_fret_likelihood,
    )
    left_hand_cost = 0.0 if likelihood is None else -(left_hand_weight * likelihood)
    total_cost = base_cost + left_hand_cost
    sequence_cost = previous_sequence_cost + total_cost
    return CandidateScoreBreakdown(
        candidate=candidate,
        base_cost=base_cost,
        initial_fret_cost=initial_fret_cost,
        fret_movement_cost=fret_movement_cost,
        string_movement_cost=string_movement_cost,
        position_shift_cost=position_shift_cost,
        candidate_position_box_start=candidate_position_box_start,
        previous_position_box_start=previous_position_box_start,
        position_box_shift_cost=position_box_shift_cost,
        repeated_note_switch_cost=repeated_note_switch_cost,
        open_string_cost=open_string_cost,
        high_fret_cost=high_fret_cost,
        left_hand_likelihood=likelihood,
        left_hand_cost=left_hand_cost,
        total_cost=total_cost,
        sequence_cost=sequence_cost,
        tie_break_fret=candidate.fret,
        tie_break_string=candidate.string,
        previous_candidate=previous_candidate,
    )


def _position_box_start(fret: int) -> int | None:
    if fret == 0:
        return None
    return ((fret - 1) // 4) * 4 + 1


def _candidate_from_decoded_event(
    event: DecodedTabEvent | None,
) -> StringFretCandidate | None:
    if event is None:
        return None
    return StringFretCandidate(
        string=event.string,
        fret=event.fret,
        pitch_midi=event.pitch_midi,
    )


def _best_score_for_candidate(
    candidate: StringFretCandidate,
    previous_layer: list[_PathState] | None,
    *,
    left_hand_fret_likelihood: LeftHandFretLikelihood | None,
    left_hand_weight: float,
    weights: ErgonomicDecoderWeights,
) -> tuple[CandidateScoreBreakdown, int | None]:
    if previous_layer is None:
        return (
            _candidate_score_breakdown(
                candidate,
                previous_candidate=None,
                previous_pitch_midi=None,
                previous_sequence_cost=0.0,
                left_hand_fret_likelihood=left_hand_fret_likelihood,
                left_hand_weight=left_hand_weight,
                weights=weights,
            ),
            None,
        )

    scored_predecessors = [
        (
            _candidate_score_breakdown(
                candidate,
                previous_candidate=previous_state.score.candidate,
                previous_pitch_midi=previous_state.score.candidate.pitch_midi,
                previous_sequence_cost=previous_state.score.sequence_cost,
                left_hand_fret_likelihood=left_hand_fret_likelihood,
                left_hand_weight=left_hand_weight,
                weights=weights,
            ),
            index,
        )
        for index, previous_state in enumerate(previous_layer)
    ]
    return min(
        scored_predecessors,
        key=lambda item: _sequence_cost_tuple(item[0]),
    )


def _sequence_cost_tuple(score: CandidateScoreBreakdown) -> tuple[float, int, int]:
    return (score.sequence_cost, score.tie_break_fret, score.tie_break_string)


def _state_sequence_cost_tuple(state: _PathState) -> tuple[float, int, int]:
    return _sequence_cost_tuple(state.score)


def _top_k_state_order(
    state: _TopKPathState,
) -> tuple[float, int, int, tuple[tuple[int, int], ...]]:
    return (
        state.sequence_cost,
        state.candidate.fret,
        state.candidate.string,
        state.path_key,
    )


def _selected_path_indices(layers: list[list[_PathState]]) -> list[int]:
    if not layers:
        return []

    selected_indices = [0] * len(layers)
    selected_index = min(
        range(len(layers[-1])),
        key=lambda index: _state_sequence_cost_tuple(layers[-1][index]),
    )
    for layer_index in range(len(layers) - 1, -1, -1):
        selected_indices[layer_index] = selected_index
        previous_index = layers[layer_index][selected_index].previous_index
        if previous_index is None:
            break
        selected_index = previous_index
    return selected_indices


def _decoded_event_from_score(
    note: NoteEvent,
    score: CandidateScoreBreakdown,
) -> DecodedTabEvent:
    selected = score.candidate
    return DecodedTabEvent(
        start=note.start,
        end=note.end,
        string=selected.string,
        fret=selected.fret,
        pitch_midi=note.pitch_midi,
        confidence=min(
            note.confidence,
            _confidence_for_cost(score.cost_tuple),
        ),
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


def _playable_notes_and_candidates(
    notes: Sequence[NoteEvent],
    *,
    first_position: FingeringPosition | None = None,
) -> list[tuple[NoteEvent, tuple[StringFretCandidate, ...]]]:
    playable: list[tuple[NoteEvent, tuple[StringFretCandidate, ...]]] = []
    for note in notes:
        candidates = candidate_positions_for_midi(note.pitch_midi)
        if candidates:
            if first_position is not None and not playable:
                candidates = _candidates_matching_first_position(
                    note,
                    candidates,
                    first_position,
                )
            playable.append((note, candidates))
    return playable


def _candidates_matching_first_position(
    note: NoteEvent,
    candidates: tuple[StringFretCandidate, ...],
    first_position: FingeringPosition,
) -> tuple[StringFretCandidate, ...]:
    matching = tuple(
        candidate
        for candidate in candidates
        if candidate.string == first_position.string
        and candidate.fret == first_position.fret
    )
    if matching:
        return matching
    raise ValueError(
        "first_position "
        f"{first_position.string}s-{first_position.fret}f is not compatible "
        f"with first playable note pitch_midi={note.pitch_midi}"
    )


def _dedupe_top_k_states(
    states: Sequence[_TopKPathState],
    *,
    top_k: int,
) -> list[_TopKPathState]:
    deduped: list[_TopKPathState] = []
    seen: set[tuple[tuple[int, int], ...]] = set()
    for state in sorted(states, key=_top_k_state_order):
        if state.path_key in seen:
            continue
        seen.add(state.path_key)
        deduped.append(state)
        if len(deduped) == top_k:
            break
    return deduped


def _candidate_from_state(
    state: _TopKPathState | None,
) -> StringFretCandidate | None:
    if state is None:
        return None
    return state.candidate


def decode_audio_notes(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
    weights: ErgonomicDecoderWeights = ErgonomicDecoderWeights(),
) -> list[DecodedTabEvent]:
    """Decode monophonic note events into one TAB position per note.

    Notes without any playable standard-tuning candidate are skipped. Polyphony,
    right-hand evidence, tapping, and left-handed player support are outside this
    baseline. Left-hand fret likelihood is optional evidence keyed by note start
    time; omitting it preserves audio-only behavior.
    """

    debug_events = decode_audio_notes_with_debug(
        notes,
        left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
        left_hand_weight=left_hand_weight,
        first_position=first_position,
        weights=weights,
    )
    return [debug_event.selected for debug_event in debug_events]


def decode_audio_notes_top_k(
    notes: Sequence[NoteEvent],
    *,
    top_k: int,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
    weights: ErgonomicDecoderWeights = ErgonomicDecoderWeights(),
) -> tuple[DecodedTabCandidate, ...]:
    """Return up to `top_k` distinct deterministic TAB candidate paths.

    This keeps the single-best decoder unchanged. This is a deterministic
    beam-style search: at each note it keeps up to `top_k` distinct partial
    paths after sorting and deduplication, then returns distinct complete
    string/fret paths ordered by total sequence cost and deterministic
    tie-breakers. It is not an exhaustive global top-k enumeration of every
    possible complete path.
    """

    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if left_hand_weight < 0:
        raise ValueError("left_hand_weight must be non-negative")

    playable = _playable_notes_and_candidates(notes, first_position=first_position)
    if not playable:
        return ()

    previous_states: list[_TopKPathState] = []
    for note, candidates in playable:
        left_hand_fret_likelihood = _left_hand_likelihood_for_note(
            note,
            left_hand_fret_likelihood_by_time,
        )
        states_for_layer: list[_TopKPathState] = []
        for candidate in candidates:
            candidate_states: list[_TopKPathState] = []
            if not previous_states:
                score = _candidate_score_breakdown(
                    candidate,
                    previous_candidate=None,
                    previous_pitch_midi=None,
                    previous_sequence_cost=0.0,
                    left_hand_fret_likelihood=left_hand_fret_likelihood,
                    left_hand_weight=left_hand_weight,
                    weights=weights,
                )
                candidate_states.append(_TopKPathState(scores=(score,)))
            else:
                for previous_state in previous_states:
                    score = _candidate_score_breakdown(
                        candidate,
                        previous_candidate=_candidate_from_state(previous_state),
                        previous_pitch_midi=previous_state.candidate.pitch_midi,
                        previous_sequence_cost=previous_state.sequence_cost,
                        left_hand_fret_likelihood=left_hand_fret_likelihood,
                        left_hand_weight=left_hand_weight,
                        weights=weights,
                    )
                    candidate_states.append(
                        _TopKPathState(scores=previous_state.scores + (score,))
                    )

            states_for_layer.extend(
                _dedupe_top_k_states(candidate_states, top_k=top_k)
            )

        previous_states = _dedupe_top_k_states(states_for_layer, top_k=top_k)

    ranked_states = _dedupe_top_k_states(previous_states, top_k=top_k)
    candidates: list[DecodedTabCandidate] = []
    playable_notes = [note for note, _ in playable]
    for rank, state in enumerate(ranked_states, start=1):
        events = tuple(
            _decoded_event_from_score(note, score)
            for note, score in zip(playable_notes, state.scores, strict=True)
        )
        candidates.append(
            DecodedTabCandidate(
                events=events,
                total_score=state.sequence_cost,
                rank=rank,
            )
        )
    return tuple(candidates)


def decode_audio_notes_with_debug(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
    weights: ErgonomicDecoderWeights = ErgonomicDecoderWeights(),
) -> tuple[DecodedNoteDebug, ...]:
    """Decode notes and return per-candidate score breakdowns.

    The decoder uses a small Viterbi-style dynamic program over playable
    string/fret candidates. `left_hand_weight` controls how strongly a fretted
    candidate is favored when left-hand likelihood is present for the note's
    start time. The left-hand contribution is `-left_hand_weight * likelihood`.
    """

    if left_hand_weight < 0:
        raise ValueError("left_hand_weight must be non-negative")

    playable_notes: list[NoteEvent] = []
    candidate_scores_by_note: list[tuple[CandidateScoreBreakdown, ...]] = []
    layers: list[list[_PathState]] = []

    for note, candidates in _playable_notes_and_candidates(
        notes,
        first_position=first_position,
    ):

        left_hand_fret_likelihood = _left_hand_likelihood_for_note(
            note,
            left_hand_fret_likelihood_by_time,
        )
        previous_layer = layers[-1] if layers else None
        candidate_scores: list[CandidateScoreBreakdown] = []
        states: list[_PathState] = []
        for candidate in candidates:
            score, previous_index = _best_score_for_candidate(
                candidate,
                previous_layer,
                left_hand_fret_likelihood=left_hand_fret_likelihood,
                left_hand_weight=left_hand_weight,
                weights=weights,
            )
            candidate_scores.append(score)
            states.append(_PathState(score=score, previous_index=previous_index))

        playable_notes.append(note)
        candidate_scores_by_note.append(tuple(candidate_scores))
        layers.append(states)

    selected_indices = _selected_path_indices(layers)
    debug_events: list[DecodedNoteDebug] = []
    for note, candidate_scores, layer, selected_index in zip(
        playable_notes,
        candidate_scores_by_note,
        layers,
        selected_indices,
        strict=True,
    ):
        selected_score = layer[selected_index].score
        debug_events.append(
            DecodedNoteDebug(
                note=note,
                selected=_decoded_event_from_score(note, selected_score),
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
    "DecodedTabCandidate",
    "ErgonomicDecoderWeights",
    "FRET_MOVEMENT_COST_WEIGHT",
    "FingeringPosition",
    "HIGH_FRET_COST_WEIGHT",
    "INITIAL_FRET_COST_WEIGHT",
    "LeftHandFretLikelihood",
    "LeftHandFretLikelihoodByTime",
    "OPEN_STRING_COST_WEIGHT",
    "POSITION_BOX_SHIFT_COST_WEIGHT",
    "POSITION_SHIFT_COST_WEIGHT",
    "REPEATED_NOTE_SWITCH_COST_WEIGHT",
    "STRING_MOVEMENT_COST_WEIGHT",
    "decode_audio_notes",
    "decode_audio_notes_top_k",
    "decode_audio_notes_with_debug",
    "parse_fingering_position",
]
