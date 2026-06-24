import json

import pytest

from guitar_tab_agent.schema import FretboardCalibration, HandLandmarkFrame
from guitar_tab_agent.video.fretboard_transform import (
    load_fretboard_calibration_json,
    transform_hand_landmark_frame_to_fretboard,
)
from guitar_tab_agent.workflows import (
    hand_landmark_frames_to_left_hand_likelihood_records,
)


def calibration_dict() -> dict[str, object]:
    return {
        "nut_string_6": [0.0, 0.0],
        "nut_string_1": [0.0, 1.0],
        "bridge_string_6": [1.0, 0.0],
        "bridge_string_1": [1.0, 1.0],
        "timestamp": 0.0,
    }


def test_load_fretboard_calibration_json_parses_valid_calibration(tmp_path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps(calibration_dict()), encoding="utf-8")

    assert load_fretboard_calibration_json(path) == FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
        timestamp=0.0,
    )


def test_load_fretboard_calibration_json_rejects_malformed_json(tmp_path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid fretboard calibration JSON"):
        load_fretboard_calibration_json(path)


def test_load_fretboard_calibration_json_rejects_missing_points(tmp_path) -> None:
    path = tmp_path / "calibration.json"
    data = calibration_dict()
    del data["bridge_string_1"]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="missing fretboard calibration point"):
        load_fretboard_calibration_json(path)


def test_load_fretboard_calibration_json_rejects_invalid_point_shape(tmp_path) -> None:
    path = tmp_path / "calibration.json"
    data = calibration_dict()
    data["nut_string_6"] = [0.0]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="nut_string_6 must be a two-element"):
        load_fretboard_calibration_json(path)


def test_load_fretboard_calibration_json_rejects_degenerate_geometry(tmp_path) -> None:
    path = tmp_path / "calibration.json"
    data = calibration_dict()
    data.update(
        {
            "nut_string_6": [0.0, 0.0],
            "nut_string_1": [0.0, 1.0],
            "bridge_string_6": [0.0, 0.0],
            "bridge_string_1": [0.0, 1.0],
        }
    )
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="degenerate"):
        load_fretboard_calibration_json(path)


def test_axis_aligned_calibration_maps_image_to_expected_fretboard_coordinates() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
    )
    frame = HandLandmarkFrame(
        timestamp=1.0,
        landmarks=(("left:index_finger_tip", 0.75, 0.25),),
        confidence=0.8,
    )

    transformed = transform_hand_landmark_frame_to_fretboard(frame, calibration)

    assert transformed.timestamp == 1.0
    assert transformed.confidence == 0.8
    assert transformed.landmarks == (("left:index_finger_tip", 0.75, 0.25),)


def test_centered_calibration_maps_center_to_midline_v() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
    )
    frame = HandLandmarkFrame(
        timestamp=1.0,
        landmarks=(("left:index_finger_tip", 0.75, 0.5),),
    )

    transformed = transform_hand_landmark_frame_to_fretboard(frame, calibration)

    assert transformed.landmarks == (("left:index_finger_tip", 0.75, 0.5),)


def test_out_of_board_points_remain_representable() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
    )
    frame = HandLandmarkFrame(
        timestamp=0.0,
        landmarks=(("left:index_finger_tip", 1.2, 1.5),),
    )

    transformed = transform_hand_landmark_frame_to_fretboard(frame, calibration)

    assert transformed.landmarks == (("left:index_finger_tip", 1.2, 1.5),)


def test_fret_nine_center_maps_to_expected_normalized_u() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
    )
    fret_nine_center_u = (9.0 - 0.5) / 24.0
    frame = HandLandmarkFrame(
        timestamp=1.0,
        landmarks=(("left:index_finger_tip", fret_nine_center_u, 0.5),),
    )

    transformed = transform_hand_landmark_frame_to_fretboard(frame, calibration)

    _, u, v = transformed.landmarks[0]
    assert u == pytest.approx(fret_nine_center_u)
    assert v == pytest.approx(0.5)


def test_calibrated_landmarks_feed_left_hand_likelihood_workflow() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(10.0, 20.0),
        nut_string_1=(10.0, 120.0),
        bridge_string_6=(250.0, 20.0),
        bridge_string_1=(250.0, 120.0),
    )
    fret_nine_center_u = (9.0 - 0.5) / 24.0
    frame = HandLandmarkFrame(
        timestamp=1.0,
        landmarks=(
            (
                "left:index_finger_tip",
                10.0 + (fret_nine_center_u * 240.0),
                70.0,
            ),
        ),
    )

    transformed = transform_hand_landmark_frame_to_fretboard(frame, calibration)
    records = hand_landmark_frames_to_left_hand_likelihood_records(
        [transformed],
        max_fret=24,
    )

    likelihood = records[0]["likelihood"]
    assert max(likelihood, key=likelihood.get) == "9"
