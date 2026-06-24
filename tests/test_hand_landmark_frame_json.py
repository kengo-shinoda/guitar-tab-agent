import json

import pytest

from guitar_tab_agent.schema import HandLandmarkFrame
from guitar_tab_agent.video.hand_landmark_frame_json import (
    load_hand_landmark_frames_json,
)


def test_load_hand_landmark_frames_json_parses_valid_frames(tmp_path) -> None:
    path = tmp_path / "landmarks.json"
    path.write_text(
        json.dumps(
            [
                {
                    "timestamp": 1.23,
                    "landmarks": [["left:index_finger_tip", 0.38, 0.52]],
                    "confidence": 0.9,
                }
            ]
        ),
        encoding="utf-8",
    )

    assert load_hand_landmark_frames_json(path) == [
        HandLandmarkFrame(
            timestamp=1.23,
            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
            confidence=0.9,
        )
    ]


def test_load_hand_landmark_frames_json_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "landmarks.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid HandLandmarkFrame JSON"):
        load_hand_landmark_frames_json(path)


def test_load_hand_landmark_frames_json_rejects_non_list_input(tmp_path) -> None:
    path = tmp_path / "landmarks.json"
    path.write_text(json.dumps({"timestamp": 0.0}), encoding="utf-8")

    with pytest.raises(ValueError, match="expected a JSON list"):
        load_hand_landmark_frames_json(path)


def test_load_hand_landmark_frames_json_rejects_invalid_frame_records(tmp_path) -> None:
    path = tmp_path / "landmarks.json"
    path.write_text(json.dumps(["not an object"]), encoding="utf-8")

    with pytest.raises(ValueError, match="record at index 0 must be an object"):
        load_hand_landmark_frames_json(path)


def test_load_hand_landmark_frames_json_rejects_invalid_landmarks(tmp_path) -> None:
    path = tmp_path / "landmarks.json"
    path.write_text(
        json.dumps([{"timestamp": 0.0, "landmarks": [["left:index_finger_tip"]]}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid HandLandmarkFrame record at index 0"):
        load_hand_landmark_frames_json(path)
