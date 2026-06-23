import pytest

import guitar_tab_agent.fusion.simple_decoder as simple_decoder
from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    decode_audio_notes,
    decode_audio_notes_with_debug,
)
from guitar_tab_agent.schema import DecodedTabEvent, NoteEvent, StringFretCandidate


def note(start: float, pitch_midi: int, confidence: float = 1.0) -> NoteEvent:
    return NoteEvent(
        start=start,
        end=start + 0.25,
        pitch_midi=pitch_midi,
        confidence=confidence,
        source="test",
    )


def positions(events: list[DecodedTabEvent]) -> list[tuple[int, int, int]]:
    return [(event.string, event.fret, event.pitch_midi) for event in events]


def test_empty_input_returns_empty_list() -> None:
    assert decode_audio_notes([]) == []


def test_single_note_uses_explicit_first_note_cost() -> None:
    decoded = decode_audio_notes([note(0.0, 64)])

    assert positions(decoded) == [(1, 0, 64)]
    assert decoded[0].confidence == 1.0


def test_repeated_notes_keep_same_position() -> None:
    decoded = decode_audio_notes([note(0.0, 64), note(0.5, 64)])

    assert positions(decoded) == [(1, 0, 64), (1, 0, 64)]
    assert decoded[1].confidence == 1.0


def test_simple_scale_like_movement_prefers_small_fret_motion() -> None:
    decoded = decode_audio_notes(
        [
            note(0.0, 64),
            note(0.5, 65),
            note(1.0, 67),
        ]
    )

    assert positions(decoded) == [
        (1, 0, 64),
        (1, 1, 65),
        (1, 3, 67),
    ]
    assert decoded[1].confidence < decoded[0].confidence


def test_duplicated_pitch_candidates_are_decoded_by_cost_not_list_order() -> None:
    decoded = decode_audio_notes(
        [
            note(0.0, 62),
            note(0.5, 64),
        ]
    )

    assert positions(decoded) == [
        (2, 3, 62),
        (2, 5, 64),
    ]


def test_left_hand_likelihood_can_select_higher_fret_pitch_candidate() -> None:
    decoded = decode_audio_notes(
        [note(0.0, 68)],
        left_hand_fret_likelihood_by_time={0.0: {9: 1.0}},
    )

    assert positions(decoded) == [(2, 9, 68)]


def test_left_hand_likelihood_can_favor_fretted_candidate_over_open_string() -> None:
    decoded = decode_audio_notes(
        [note(0.0, 64)],
        left_hand_fret_likelihood_by_time={0.0: {9: 1.0}},
        left_hand_weight=10.0,
    )

    assert positions(decoded) == [(3, 9, 64)]


def test_no_left_hand_evidence_preserves_audio_only_output() -> None:
    notes = [
        note(0.0, 64),
        note(0.5, 68),
    ]

    assert decode_audio_notes(
        notes,
        left_hand_fret_likelihood_by_time=None,
    ) == decode_audio_notes(notes)


def test_missing_left_hand_likelihood_for_note_time_preserves_output() -> None:
    notes = [
        note(0.0, 64),
        note(0.5, 68),
    ]

    assert decode_audio_notes(
        notes,
        left_hand_fret_likelihood_by_time={99.0: {9: 1.0}},
    ) == decode_audio_notes(notes)


def test_left_hand_score_components_are_inspectable() -> None:
    debug_events = decode_audio_notes_with_debug(
        [note(0.0, 68)],
        left_hand_fret_likelihood_by_time={0.0: {9: 1.0}},
    )

    assert positions([debug_events[0].selected]) == [(2, 9, 68)]
    selected_score = next(
        score
        for score in debug_events[0].candidate_scores
        if score.candidate.string == 2 and score.candidate.fret == 9
    )
    assert selected_score.base_cost == 9.0
    assert selected_score.left_hand_likelihood == 1.0
    assert selected_score.left_hand_cost == -DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT
    assert selected_score.total_cost == 3.0


def test_left_hand_weight_must_be_non_negative() -> None:
    with pytest.raises(ValueError, match="left_hand_weight must be non-negative"):
        decode_audio_notes(
            [note(0.0, 68)],
            left_hand_fret_likelihood_by_time={0.0: {9: 1.0}},
            left_hand_weight=-1.0,
        )


def test_tie_breaking_prefers_lower_fret_then_lower_string_number(monkeypatch) -> None:
    def fake_candidates(pitch_midi: int) -> tuple[StringFretCandidate, ...]:
        if pitch_midi == 50:
            return (StringFretCandidate(string=3, fret=5, pitch_midi=50),)
        return (
            StringFretCandidate(string=2, fret=6, pitch_midi=pitch_midi),
            StringFretCandidate(string=4, fret=4, pitch_midi=pitch_midi),
        )

    monkeypatch.setattr(simple_decoder, "candidate_positions_for_midi", fake_candidates)

    decoded = decode_audio_notes(
        [
            note(0.0, 50),
            note(0.5, 60),
        ]
    )

    assert positions(decoded) == [
        (3, 5, 50),
        (4, 4, 60),
    ]


def test_tie_breaking_prefers_lower_string_when_fret_ties(monkeypatch) -> None:
    def fake_candidates(pitch_midi: int) -> tuple[StringFretCandidate, ...]:
        if pitch_midi == 50:
            return (StringFretCandidate(string=3, fret=5, pitch_midi=50),)
        return (
            StringFretCandidate(string=4, fret=4, pitch_midi=pitch_midi),
            StringFretCandidate(string=2, fret=4, pitch_midi=pitch_midi),
        )

    monkeypatch.setattr(simple_decoder, "candidate_positions_for_midi", fake_candidates)

    decoded = decode_audio_notes(
        [
            note(0.0, 50),
            note(0.5, 60),
        ]
    )

    assert positions(decoded) == [
        (3, 5, 50),
        (2, 4, 60),
    ]


def test_unplayable_notes_are_skipped() -> None:
    decoded = decode_audio_notes([note(0.0, 39), note(0.5, 40)])

    assert positions(decoded) == [(6, 0, 40)]
