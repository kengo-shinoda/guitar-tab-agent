import json

import pytest

from guitar_tab_agent.schema import HandLandmarkFrame
from guitar_tab_agent.workflows import (
    hand_landmark_frames_to_left_hand_likelihood_json,
    hand_landmark_frames_to_left_hand_likelihood_records,
)


def _center(fret: int, *, max_fret: int) -> float:
    return (fret - 0.5) / max_fret


def test_hand_landmark_frames_convert_to_left_hand_likelihood_records() -> None:
    max_fret = 12
    frames = [
        HandLandmarkFrame(
            timestamp=1.23,
            landmarks=(
                ("left:index_finger_tip", _center(5, max_fret=max_fret), 0.52),
            ),
            confidence=0.9,
        )
    ]

    records = hand_landmark_frames_to_left_hand_likelihood_records(
        frames,
        max_fret=max_fret,
    )

    assert records[0]["time"] == 1.23
    likelihood = records[0]["likelihood"]
    assert isinstance(likelihood, dict)
    assert max(likelihood, key=likelihood.get) == "5"
    assert likelihood["5"] == pytest.approx(1.0)


def test_hand_landmark_conversion_ignores_right_hand_landmarks() -> None:
    max_fret = 12
    frame = HandLandmarkFrame(
        timestamp=0.0,
        landmarks=(("right:index_finger_tip", _center(5, max_fret=max_fret), 0.5),),
    )

    assert hand_landmark_frames_to_left_hand_likelihood_records(
        [frame],
        max_fret=max_fret,
    ) == [{"time": 0.0, "likelihood": {}}]


def test_hand_landmark_conversion_empty_for_missing_or_out_of_fretboard_fingertips() -> None:
    frames = [
        HandLandmarkFrame(timestamp=0.0, landmarks=()),
        HandLandmarkFrame(
            timestamp=0.5,
            landmarks=(("left:index_finger_tip", 1.2, 0.5),),
        ),
    ]

    assert hand_landmark_frames_to_left_hand_likelihood_records(frames) == [
        {"time": 0.0, "likelihood": {}},
        {"time": 0.5, "likelihood": {}},
    ]


def test_hand_landmark_conversion_json_is_deterministic() -> None:
    max_fret = 4
    frames = [
        HandLandmarkFrame(
            timestamp=0.0,
            landmarks=(("left:index_finger_tip", _center(2, max_fret=max_fret), 0.5),),
        )
    ]

    first = hand_landmark_frames_to_left_hand_likelihood_json(
        frames,
        max_fret=max_fret,
    )
    second = hand_landmark_frames_to_left_hand_likelihood_json(
        frames,
        max_fret=max_fret,
    )

    assert first == second
    assert list(json.loads(first)[0]["likelihood"].keys()) == ["1", "2", "3", "4"]


def test_hand_landmark_conversion_rejects_invalid_max_fret() -> None:
    with pytest.raises(ValueError, match="max_fret must be positive"):
        hand_landmark_frames_to_left_hand_likelihood_records([], max_fret=0)
