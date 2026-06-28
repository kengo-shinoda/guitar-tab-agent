import pytest

import guitar_tab_agent.fusion.simple_decoder as simple_decoder
from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    ErgonomicDecoderWeights,
    FingeringPosition,
    decode_audio_notes,
    decode_audio_notes_top_k,
    decode_audio_notes_with_debug,
    parse_fingering_position,
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


def test_parse_fingering_position_accepts_compact_hint() -> None:
    assert parse_fingering_position("5s-0f") == FingeringPosition(string=5, fret=0)


def test_parse_fingering_position_rejects_malformed_hint() -> None:
    with pytest.raises(ValueError, match="first_position must use format"):
        parse_fingering_position("5-0")


def test_first_position_hint_can_select_audio_ambiguous_start() -> None:
    notes = [
        note(0.0, 66),
        note(0.25, 67),
        note(0.5, 68),
        note(0.75, 69),
    ]

    default_candidates = decode_audio_notes_top_k(notes, top_k=2)
    hinted_candidates = decode_audio_notes_top_k(
        notes,
        top_k=2,
        first_position=FingeringPosition(string=2, fret=7),
    )

    assert positions(list(default_candidates[0].events))[0] == (1, 2, 66)
    assert positions(list(hinted_candidates[0].events))[0] == (2, 7, 66)


def test_no_first_position_hint_preserves_top_k_behavior() -> None:
    notes = [
        note(0.0, 66),
        note(0.25, 67),
        note(0.5, 68),
        note(0.75, 69),
    ]

    assert decode_audio_notes_top_k(notes, top_k=3, first_position=None) == (
        decode_audio_notes_top_k(notes, top_k=3)
    )


def test_first_position_hint_rejects_pitch_incompatible_start() -> None:
    with pytest.raises(ValueError, match="not compatible"):
        decode_audio_notes_top_k(
            [note(0.0, 66)],
            top_k=2,
            first_position=FingeringPosition(string=5, fret=0),
        )


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
    assert selected_score.initial_fret_cost == 9.0
    assert selected_score.high_fret_cost == pytest.approx(0.45)
    assert selected_score.base_cost == pytest.approx(9.45)
    assert selected_score.left_hand_likelihood == 1.0
    assert selected_score.left_hand_cost == -DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT
    assert selected_score.total_cost == pytest.approx(3.45)
    assert selected_score.sequence_cost == pytest.approx(3.45)


def test_high_fret_extra_penalty_starts_above_threshold() -> None:
    debug_events = decode_audio_notes_with_debug([note(0.0, 82)])

    string_1_fret_18_score = next(
        score
        for score in debug_events[0].candidate_scores
        if score.candidate.string == 1 and score.candidate.fret == 18
    )

    assert string_1_fret_18_score.high_fret_cost == pytest.approx(1.05)


def test_non_first_string_very_high_fret_gets_extra_penalty() -> None:
    debug_events = decode_audio_notes_with_debug([note(0.0, 80)])

    string_2_fret_21_score = next(
        score
        for score in debug_events[0].candidate_scores
        if score.candidate.string == 2 and score.candidate.fret == 21
    )

    assert string_2_fret_21_score.high_fret_cost == pytest.approx(4.65)


def test_global_path_can_choose_slightly_worse_start_for_better_phrase(
    monkeypatch,
) -> None:
    def fake_candidates(pitch_midi: int) -> tuple[StringFretCandidate, ...]:
        if pitch_midi == 50:
            return (
                StringFretCandidate(string=1, fret=0, pitch_midi=pitch_midi),
                StringFretCandidate(string=3, fret=7, pitch_midi=pitch_midi),
            )
        if pitch_midi == 51:
            return (
                StringFretCandidate(string=1, fret=12, pitch_midi=pitch_midi),
                StringFretCandidate(string=3, fret=8, pitch_midi=pitch_midi),
            )
        return (
            StringFretCandidate(string=1, fret=12, pitch_midi=pitch_midi),
            StringFretCandidate(string=3, fret=9, pitch_midi=pitch_midi),
        )

    monkeypatch.setattr(simple_decoder, "candidate_positions_for_midi", fake_candidates)

    decoded = decode_audio_notes(
        [
            note(0.0, 50),
            note(0.5, 51),
            note(1.0, 52),
        ]
    )

    assert positions(decoded) == [
        (3, 7, 50),
        (3, 8, 51),
        (3, 9, 52),
    ]


def test_position_box_continuity_keeps_nine_to_twelve_across_strings() -> None:
    midi_sequence = [
        73,
        74,
        75,
        76,
        68,
        69,
        70,
        71,
        64,
        65,
        66,
        67,
        59,
        60,
        61,
        62,
    ]

    decoded = decode_audio_notes(
        [
            note(index * 0.25, pitch_midi)
            for index, pitch_midi in enumerate(midi_sequence)
        ]
    )

    assert positions(decoded) == [
        (1, 9, 73),
        (1, 10, 74),
        (1, 11, 75),
        (1, 12, 76),
        (2, 9, 68),
        (2, 10, 69),
        (2, 11, 70),
        (2, 12, 71),
        (3, 9, 64),
        (3, 10, 65),
        (3, 11, 66),
        (3, 12, 67),
        (4, 9, 59),
        (4, 10, 60),
        (4, 11, 61),
        (4, 12, 62),
    ]


def test_position_box_shift_cost_is_inspectable(monkeypatch) -> None:
    calls = 0

    def fake_candidates(pitch_midi: int) -> tuple[StringFretCandidate, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return (StringFretCandidate(string=2, fret=9, pitch_midi=pitch_midi),)
        return (
            StringFretCandidate(string=1, fret=5, pitch_midi=pitch_midi),
            StringFretCandidate(string=2, fret=10, pitch_midi=pitch_midi),
        )

    monkeypatch.setattr(simple_decoder, "candidate_positions_for_midi", fake_candidates)

    debug_events = decode_audio_notes_with_debug([note(0.0, 68), note(0.5, 69)])
    shifted_score = next(
        score
        for score in debug_events[1].candidate_scores
        if score.candidate.string == 1 and score.candidate.fret == 5
    )

    assert shifted_score.previous_position_box_start == 9
    assert shifted_score.candidate_position_box_start == 5
    assert shifted_score.position_box_shift_cost == 2.0


def test_repeated_note_switch_penalty_is_inspectable(monkeypatch) -> None:
    calls = 0

    def fake_candidates(pitch_midi: int) -> tuple[StringFretCandidate, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return (StringFretCandidate(string=1, fret=5, pitch_midi=pitch_midi),)
        return (
            StringFretCandidate(string=1, fret=5, pitch_midi=pitch_midi),
            StringFretCandidate(string=2, fret=5, pitch_midi=pitch_midi),
        )

    monkeypatch.setattr(simple_decoder, "candidate_positions_for_midi", fake_candidates)

    debug_events = decode_audio_notes_with_debug([note(0.0, 60), note(0.5, 60)])

    assert positions([event.selected for event in debug_events]) == [
        (1, 5, 60),
        (1, 5, 60),
    ]
    switched_score = next(
        score
        for score in debug_events[1].candidate_scores
        if score.candidate.string == 2 and score.candidate.fret == 5
    )
    assert switched_score.repeated_note_switch_cost == 2.0
    assert switched_score.previous_candidate == StringFretCandidate(
        string=1,
        fret=5,
        pitch_midi=60,
    )


def test_left_hand_weight_must_be_non_negative() -> None:
    with pytest.raises(ValueError, match="left_hand_weight must be non-negative"):
        decode_audio_notes(
            [note(0.0, 68)],
            left_hand_fret_likelihood_by_time={0.0: {9: 1.0}},
            left_hand_weight=-1.0,
        )


def test_ergonomic_weights_must_be_non_negative() -> None:
    with pytest.raises(ValueError, match="fret_movement weight must be non-negative"):
        ErgonomicDecoderWeights(fret_movement=-1.0)


def test_position_box_shift_weight_must_be_non_negative() -> None:
    with pytest.raises(
        ValueError,
        match="position_box_shift weight must be non-negative",
    ):
        ErgonomicDecoderWeights(position_box_shift=-1.0)


def test_same_position_box_can_beat_lower_fret_candidate(monkeypatch) -> None:
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
        (2, 6, 60),
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


def test_top_k_returns_multiple_same_pitch_ambiguity_candidates() -> None:
    notes = [
        note(0.0, 66),
        note(0.25, 67),
        note(0.5, 68),
        note(0.75, 69),
    ]

    candidates = decode_audio_notes_top_k(notes, top_k=3)

    assert len(candidates) == 3
    assert [candidate.rank for candidate in candidates] == [1, 2, 3]
    assert [candidate.total_score for candidate in candidates] == sorted(
        candidate.total_score for candidate in candidates
    )
    candidate_positions = [positions(list(candidate.events)) for candidate in candidates]
    assert candidate_positions[0] == positions(decode_audio_notes(notes))
    assert len({tuple(path) for path in candidate_positions}) == 3
    assert any(path != candidate_positions[0] for path in candidate_positions[1:])


def test_top_k_ordering_is_deterministic() -> None:
    notes = [
        note(0.0, 66),
        note(0.25, 67),
        note(0.5, 68),
        note(0.75, 69),
    ]

    first = decode_audio_notes_top_k(notes, top_k=5)
    second = decode_audio_notes_top_k(notes, top_k=5)

    assert first == second


def test_top_k_does_not_crash_when_fewer_distinct_paths_exist() -> None:
    candidates = decode_audio_notes_top_k([note(0.0, 40)], top_k=5)

    assert len(candidates) == 1
    assert positions(list(candidates[0].events)) == [(6, 0, 40)]


def test_top_k_rejects_non_positive_request() -> None:
    with pytest.raises(ValueError, match="top_k must be positive"):
        decode_audio_notes_top_k([note(0.0, 64)], top_k=0)
