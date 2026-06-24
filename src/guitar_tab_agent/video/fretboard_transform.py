"""Manual fretboard calibration transform for hand landmarks.

This module maps image-space hand landmarks into normalized fretboard
coordinates. The MVP uses a deterministic affine approximation:

- `nut_string_6` is the origin;
- the vector from `nut_string_6` to `bridge_string_6` defines the `u` axis;
- the vector from `nut_string_6` to `nut_string_1` defines the `v` axis.

This is manual, dependency-free, and intentionally does not clamp transformed
coordinates. Downstream likelihood code can ignore points outside `[0, 1]`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from guitar_tab_agent.schema import FretboardCalibration, HandLandmarkFrame, ImagePoint


AFFINE_EPSILON = 1e-12
CALIBRATION_POINT_NAMES = (
    "nut_string_6",
    "nut_string_1",
    "bridge_string_6",
    "bridge_string_1",
)


def load_fretboard_calibration_json(path: str | Path) -> FretboardCalibration:
    """Load a flat manual `FretboardCalibration` JSON file."""

    json_path = Path(path)
    try:
        raw_calibration = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid fretboard calibration JSON in {json_path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"could not read fretboard calibration JSON {json_path}: {exc}"
        ) from exc

    calibration = fretboard_calibration_from_json_record(raw_calibration)
    _validate_affine_basis(calibration)
    return calibration


def fretboard_calibration_from_json_record(record: Any) -> FretboardCalibration:
    """Construct a schema `FretboardCalibration` from a JSON object."""

    if not isinstance(record, dict):
        raise ValueError("fretboard calibration JSON must be an object")

    missing_points = [name for name in CALIBRATION_POINT_NAMES if name not in record]
    if missing_points:
        raise ValueError(
            "missing fretboard calibration point(s): " + ", ".join(missing_points)
        )

    calibration = FretboardCalibration(
        nut_string_6=_image_point(record["nut_string_6"], field_name="nut_string_6"),
        nut_string_1=_image_point(record["nut_string_1"], field_name="nut_string_1"),
        bridge_string_6=_image_point(
            record["bridge_string_6"],
            field_name="bridge_string_6",
        ),
        bridge_string_1=_image_point(
            record["bridge_string_1"],
            field_name="bridge_string_1",
        ),
        timestamp=_optional_timestamp(record.get("timestamp")),
    )
    _validate_affine_basis(calibration)
    return calibration


def transform_hand_landmark_frame_to_fretboard(
    frame: HandLandmarkFrame,
    calibration: FretboardCalibration,
) -> HandLandmarkFrame:
    """Map one image-space frame into normalized fretboard coordinates."""

    transform = _affine_transform(calibration)
    return HandLandmarkFrame(
        timestamp=frame.timestamp,
        landmarks=tuple(
            (name, *transform((x, y))) for name, x, y in frame.landmarks
        ),
        confidence=frame.confidence,
    )


def transform_hand_landmark_frames_to_fretboard(
    frames: Sequence[HandLandmarkFrame],
    calibration: FretboardCalibration,
) -> list[HandLandmarkFrame]:
    """Map image-space frames into normalized fretboard coordinates."""

    return [
        transform_hand_landmark_frame_to_fretboard(frame, calibration)
        for frame in frames
    ]


def _image_point(value: Any, *, field_name: str) -> ImagePoint:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError(f"{field_name} must be a two-element [x, y] point")
    x, y = value
    if not _is_number(x) or not _is_number(y):
        raise ValueError(f"{field_name} coordinates must be numbers")
    return (float(x), float(y))


def _optional_timestamp(value: Any) -> float | None:
    if value is None:
        return None
    if not _is_number(value):
        raise ValueError("timestamp must be numeric")
    return float(value)


def _affine_transform(calibration: FretboardCalibration):
    nut_string_6 = _required_point(calibration.nut_string_6, "nut_string_6")
    nut_string_1 = _required_point(calibration.nut_string_1, "nut_string_1")
    bridge_string_6 = _required_point(
        calibration.bridge_string_6,
        "bridge_string_6",
    )
    _required_point(
        calibration.bridge_string_1,
        "bridge_string_1",
    )

    origin = nut_string_6
    u_axis = _subtract(bridge_string_6, nut_string_6)
    v_axis = _subtract(nut_string_1, nut_string_6)
    determinant = _determinant(u_axis, v_axis)

    if abs(determinant) <= AFFINE_EPSILON:
        raise ValueError("fretboard calibration geometry is degenerate")

    def transform(point: ImagePoint) -> tuple[float, float]:
        delta = _subtract(point, origin)
        u = _determinant(delta, v_axis) / determinant
        v = _determinant(u_axis, delta) / determinant
        return (u, v)

    return transform


def _validate_affine_basis(calibration: FretboardCalibration) -> None:
    nut_string_6 = _required_point(calibration.nut_string_6, "nut_string_6")
    nut_string_1 = _required_point(calibration.nut_string_1, "nut_string_1")
    bridge_string_6 = _required_point(
        calibration.bridge_string_6,
        "bridge_string_6",
    )
    bridge_string_1 = _required_point(
        calibration.bridge_string_1,
        "bridge_string_1",
    )
    area = _quadrilateral_area(
        (
            nut_string_6,
            bridge_string_6,
            bridge_string_1,
            nut_string_1,
        )
    )
    if abs(area) <= AFFINE_EPSILON:
        raise ValueError("fretboard calibration geometry is degenerate")
    _affine_transform(calibration)


def _required_point(point: ImagePoint | None, field_name: str) -> ImagePoint:
    if point is None:
        raise ValueError(f"{field_name} must be present")
    return point


def _subtract(left: ImagePoint, right: ImagePoint) -> ImagePoint:
    return (left[0] - right[0], left[1] - right[1])


def _determinant(first: ImagePoint, second: ImagePoint) -> float:
    return (first[0] * second[1]) - (first[1] * second[0])


def _quadrilateral_area(
    points: tuple[ImagePoint, ImagePoint, ImagePoint, ImagePoint],
) -> float:
    twice_area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        twice_area += (point[0] * next_point[1]) - (point[1] * next_point[0])
    return twice_area / 2.0


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = [
    "AFFINE_EPSILON",
    "CALIBRATION_POINT_NAMES",
    "fretboard_calibration_from_json_record",
    "load_fretboard_calibration_json",
    "transform_hand_landmark_frame_to_fretboard",
    "transform_hand_landmark_frames_to_fretboard",
]
