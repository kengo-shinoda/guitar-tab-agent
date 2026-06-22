import json

import pytest

from guitar_tab_agent.video.fretboard_calibration import (
    ImagePoint,
    ManualFretboardCalibration,
)


def calibration_dict() -> dict[str, object]:
    return {
        "video_id": "example",
        "frame_time": 0.0,
        "image_width": 1920,
        "image_height": 1080,
        "points": {
            "nut_string6": [100.0, 400.0],
            "nut_string1": [100.0, 700.0],
            "high_fret_string6": [1600.0, 350.0],
            "high_fret_string1": [1600.0, 750.0],
        },
    }


def test_calibration_json_round_trip(tmp_path) -> None:
    input_path = tmp_path / "calibration.json"
    output_path = tmp_path / "saved.json"
    input_path.write_text(json.dumps(calibration_dict()), encoding="utf-8")

    calibration = ManualFretboardCalibration.load_json(input_path)
    calibration.save_json(output_path)

    assert ManualFretboardCalibration.load_json(output_path) == calibration
    assert json.loads(output_path.read_text(encoding="utf-8")) == calibration.to_dict()


def test_missing_point_produces_readable_error() -> None:
    data = calibration_dict()
    points = data["points"]
    assert isinstance(points, dict)
    del points["high_fret_string1"]

    with pytest.raises(ValueError, match="missing calibration point.*high_fret_string1"):
        ManualFretboardCalibration.from_dict(data)


def test_invalid_json_produces_readable_error(tmp_path) -> None:
    input_path = tmp_path / "calibration.json"
    input_path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid calibration JSON.*line 1, column 2"):
        ManualFretboardCalibration.load_json(input_path)


def test_point_coordinates_must_be_numeric() -> None:
    data = calibration_dict()
    points = data["points"]
    assert isinstance(points, dict)
    points["nut_string6"] = ["left", 400.0]

    with pytest.raises(ValueError, match="points.nut_string6 coordinates"):
        ManualFretboardCalibration.from_dict(data)


def test_image_to_fretboard_coordinate_conventions() -> None:
    calibration = ManualFretboardCalibration(
        video_id="synthetic",
        frame_time=0.0,
        image_width=200,
        image_height=100,
        nut_string6=ImagePoint(10.0, 20.0),
        nut_string1=ImagePoint(10.0, 80.0),
        high_fret_string6=ImagePoint(110.0, 20.0),
        high_fret_string1=ImagePoint(110.0, 80.0),
    )

    nut_string6 = calibration.image_to_fretboard(ImagePoint(10.0, 20.0))
    high_fret_string6 = calibration.image_to_fretboard(ImagePoint(110.0, 20.0))
    nut_string1 = calibration.image_to_fretboard(ImagePoint(10.0, 80.0))
    center = calibration.image_to_fretboard(ImagePoint(60.0, 50.0))

    assert nut_string6.u == pytest.approx(0.0)
    assert nut_string6.v == pytest.approx(0.0)
    assert high_fret_string6.u == pytest.approx(1.0)
    assert high_fret_string6.v == pytest.approx(0.0)
    assert nut_string1.u == pytest.approx(0.0)
    assert nut_string1.v == pytest.approx(1.0)
    assert center.u == pytest.approx(0.5)
    assert center.v == pytest.approx(0.5)


def test_trapezoid_inside_point_maps_inside_unit_square() -> None:
    calibration = ManualFretboardCalibration.from_dict(calibration_dict())

    center = calibration.image_to_fretboard(ImagePoint(850.0, 550.0))

    assert 0.0 <= center.u <= 1.0
    assert 0.0 <= center.v <= 1.0


def test_degenerate_quadrilateral_is_rejected() -> None:
    data = calibration_dict()
    data["points"] = {
        "nut_string6": [100.0, 100.0],
        "nut_string1": [200.0, 200.0],
        "high_fret_string6": [300.0, 300.0],
        "high_fret_string1": [400.0, 400.0],
    }

    with pytest.raises(ValueError, match="non-zero area"):
        ManualFretboardCalibration.from_dict(data)
