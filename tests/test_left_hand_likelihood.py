import pytest

from guitar_tab_agent.schema import HandLandmarkFrame
from guitar_tab_agent.video.left_hand_likelihood import (
    estimate_left_hand_fret_likelihood,
)


def _center(fret: int, *, max_fret: int) -> float:
    return (fret - 0.5) / max_fret


def test_fingertip_near_target_fret_gets_highest_score() -> None:
    max_fret = 12
    frame = HandLandmarkFrame(
        timestamp=0.0,
        landmarks=(("left:index_finger_tip", _center(5, max_fret=max_fret), 0.5),),
    )

    scores = estimate_left_hand_fret_likelihood(frame, max_fret=max_fret)

    assert max(scores, key=scores.get) == 5
    assert scores[5] > scores[4]
    assert scores[5] > scores[6]


def test_multiple_fingertips_contribute_to_likelihood() -> None:
    max_fret = 12
    scores = estimate_left_hand_fret_likelihood(
        (
            ("left:index_finger_tip", _center(3, max_fret=max_fret), 0.25),
            ("left:ring_finger_tip", _center(7, max_fret=max_fret), 0.75),
        ),
        max_fret=max_fret,
    )

    assert scores[3] > scores[2]
    assert scores[3] > scores[4]
    assert scores[7] > scores[6]
    assert scores[7] > scores[8]


def test_missing_fingertips_return_empty_scores() -> None:
    frame = HandLandmarkFrame(timestamp=0.0, landmarks=())

    assert estimate_left_hand_fret_likelihood(frame) == {}


def test_out_of_fretboard_fingertips_are_ignored() -> None:
    scores = estimate_left_hand_fret_likelihood(
        (
            ("left:index_finger_tip", -0.1, 0.5),
            ("left:middle_finger_tip", 0.5, 1.2),
        )
    )

    assert scores == {}


def test_non_fingertip_landmarks_are_ignored() -> None:
    max_fret = 12
    scores = estimate_left_hand_fret_likelihood(
        (
            ("left:wrist", _center(2, max_fret=max_fret), 0.5),
            ("left:index_finger_tip", _center(9, max_fret=max_fret), 0.5),
        ),
        max_fret=max_fret,
    )

    assert max(scores, key=scores.get) == 9
    assert scores[2] < scores[9]


def test_landmark_names_do_not_require_hand_label_prefix() -> None:
    max_fret = 12
    scores = estimate_left_hand_fret_likelihood(
        (("middle_finger_tip", _center(4, max_fret=max_fret), 0.5),),
        max_fret=max_fret,
    )

    assert max(scores, key=scores.get) == 4


def test_explicit_right_hand_fingertip_landmarks_are_ignored() -> None:
    max_fret = 12
    scores = estimate_left_hand_fret_likelihood(
        (
            ("right:index_finger_tip", _center(4, max_fret=max_fret), 0.5),
            ("right:middle_finger_tip", _center(5, max_fret=max_fret), 0.5),
            ("right:ring_finger_tip", _center(6, max_fret=max_fret), 0.5),
            ("right:pinky_tip", _center(7, max_fret=max_fret), 0.5),
        ),
        max_fret=max_fret,
    )

    assert scores == {}


def test_output_is_stable_and_deterministic() -> None:
    landmarks = (
        ("left:index_finger_tip", 0.2, 0.4),
        ("left:pinky_tip", 0.8, 0.6),
    )

    first = estimate_left_hand_fret_likelihood(landmarks, max_fret=12)
    second = estimate_left_hand_fret_likelihood(landmarks, max_fret=12)

    assert first == second


def test_max_fret_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_fret must be positive"):
        estimate_left_hand_fret_likelihood(
            (("left:index_finger_tip", 0.2, 0.5),),
            max_fret=0,
        )
