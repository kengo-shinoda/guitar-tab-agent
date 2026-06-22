"""Manual fretboard calibration contract.

Coordinate conventions:

- Image coordinates use pixels, with `x` increasing to the right and `y`
  increasing downward.
- Normalized fretboard coordinates use `u` from nut to bridge/high-fret
  direction and `v` from the string 6 side to the string 1 side.
- Points inside the calibrated quadrilateral should map approximately into
  `[0, 1] x [0, 1]`.

This module intentionally does not extract frames, read videos, or depend on
OpenCV/MediaPipe. It only defines the small JSON contract needed before video
processing work begins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_POINT_NAMES = (
    "nut_string6",
    "nut_string1",
    "high_fret_string6",
    "high_fret_string1",
)

NEWTON_ITERATIONS = 12
NEWTON_EPSILON = 1e-12


@dataclass(frozen=True)
class ImagePoint:
    """A point in image pixel coordinates."""

    x: float
    y: float

    @classmethod
    def from_json_value(cls, value: Any, *, field_name: str) -> ImagePoint:
        if not isinstance(value, list | tuple) or len(value) != 2:
            raise ValueError(f"{field_name} must be a two-item [x, y] point")
        x, y = value
        if not isinstance(x, int | float) or not isinstance(y, int | float):
            raise ValueError(f"{field_name} coordinates must be numbers")
        return cls(float(x), float(y))

    def to_json_value(self) -> list[float]:
        return [self.x, self.y]


@dataclass(frozen=True)
class NormalizedFretboardPoint:
    """A point in normalized fretboard coordinates."""

    u: float
    v: float


@dataclass(frozen=True)
class ManualFretboardCalibration:
    """Manual fretboard calibration for one video frame.

    The four points define a quadrilateral:

    - `nut_string6`: u=0, v=0
    - `nut_string1`: u=0, v=1
    - `high_fret_string6`: u=1, v=0
    - `high_fret_string1`: u=1, v=1
    """

    video_id: str
    frame_time: float
    image_width: int
    image_height: int
    nut_string6: ImagePoint
    nut_string1: ImagePoint
    high_fret_string6: ImagePoint
    high_fret_string1: ImagePoint

    def __post_init__(self) -> None:
        if not self.video_id:
            raise ValueError("video_id must not be empty")
        if self.frame_time < 0:
            raise ValueError("frame_time must be non-negative")
        if self.image_width <= 0:
            raise ValueError("image_width must be positive")
        if self.image_height <= 0:
            raise ValueError("image_height must be positive")
        if abs(self._quadrilateral_area()) <= NEWTON_EPSILON:
            raise ValueError("calibration quadrilateral must have non-zero area")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManualFretboardCalibration:
        if not isinstance(data, dict):
            raise ValueError("calibration JSON must be an object")

        points = data.get("points")
        if not isinstance(points, dict):
            raise ValueError("calibration JSON must contain a points object")

        missing_points = [name for name in REQUIRED_POINT_NAMES if name not in points]
        if missing_points:
            raise ValueError(
                "missing calibration point(s): " + ", ".join(missing_points)
            )

        try:
            video_id = data["video_id"]
            frame_time = data["frame_time"]
            image_width = data["image_width"]
            image_height = data["image_height"]
        except KeyError as exc:
            raise ValueError(f"missing calibration field: {exc.args[0]}") from exc

        if not isinstance(video_id, str):
            raise ValueError("video_id must be a string")
        if not isinstance(frame_time, int | float):
            raise ValueError("frame_time must be a number")
        if not isinstance(image_width, int) or isinstance(image_width, bool):
            raise ValueError("image_width must be an integer")
        if not isinstance(image_height, int) or isinstance(image_height, bool):
            raise ValueError("image_height must be an integer")

        return cls(
            video_id=video_id,
            frame_time=float(frame_time),
            image_width=image_width,
            image_height=image_height,
            nut_string6=ImagePoint.from_json_value(
                points["nut_string6"], field_name="points.nut_string6"
            ),
            nut_string1=ImagePoint.from_json_value(
                points["nut_string1"], field_name="points.nut_string1"
            ),
            high_fret_string6=ImagePoint.from_json_value(
                points["high_fret_string6"], field_name="points.high_fret_string6"
            ),
            high_fret_string1=ImagePoint.from_json_value(
                points["high_fret_string1"], field_name="points.high_fret_string1"
            ),
        )

    @classmethod
    def load_json(cls, path: str | Path) -> ManualFretboardCalibration:
        json_path = Path(path)
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid calibration JSON in {json_path}: {exc.msg} "
                f"(line {exc.lineno}, column {exc.colno})"
            ) from exc
        except OSError as exc:
            raise ValueError(f"could not read calibration JSON {json_path}: {exc}") from exc

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "frame_time": self.frame_time,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "points": {
                "nut_string6": self.nut_string6.to_json_value(),
                "nut_string1": self.nut_string1.to_json_value(),
                "high_fret_string6": self.high_fret_string6.to_json_value(),
                "high_fret_string1": self.high_fret_string1.to_json_value(),
            },
        }

    def save_json(self, path: str | Path) -> None:
        json_path = Path(path)
        try:
            json_path.write_text(
                json.dumps(self.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ValueError(f"could not write calibration JSON {json_path}: {exc}") from exc

    def image_to_fretboard(self, point: ImagePoint) -> NormalizedFretboardPoint:
        """Map an image point to normalized fretboard coordinates.

        The inverse mapping is solved against the bilinear quadrilateral formed
        by the four manual calibration points. It is exact for rectangular and
        parallelogram-like synthetic fixtures and stable enough for the manual
        calibration contract.
        """

        u = 0.5
        v = 0.5
        for _ in range(NEWTON_ITERATIONS):
            mapped = self._fretboard_to_image(u, v)
            residual_x = mapped.x - point.x
            residual_y = mapped.y - point.y

            du = self._derivative_u(v)
            dv = self._derivative_v(u)
            determinant = (du.x * dv.y) - (du.y * dv.x)
            if abs(determinant) <= NEWTON_EPSILON:
                break

            delta_u = ((residual_x * dv.y) - (residual_y * dv.x)) / determinant
            delta_v = ((du.x * residual_y) - (du.y * residual_x)) / determinant
            u -= delta_u
            v -= delta_v

            if abs(delta_u) <= NEWTON_EPSILON and abs(delta_v) <= NEWTON_EPSILON:
                break

        return NormalizedFretboardPoint(u=u, v=v)

    def _fretboard_to_image(self, u: float, v: float) -> ImagePoint:
        top = _interpolate(self.nut_string6, self.high_fret_string6, u)
        bottom = _interpolate(self.nut_string1, self.high_fret_string1, u)
        return _interpolate(top, bottom, v)

    def _derivative_u(self, v: float) -> ImagePoint:
        string6_delta = _subtract(self.high_fret_string6, self.nut_string6)
        string1_delta = _subtract(self.high_fret_string1, self.nut_string1)
        return _interpolate(string6_delta, string1_delta, v)

    def _derivative_v(self, u: float) -> ImagePoint:
        nut_delta = _subtract(self.nut_string1, self.nut_string6)
        high_fret_delta = _subtract(self.high_fret_string1, self.high_fret_string6)
        return _interpolate(nut_delta, high_fret_delta, u)

    def _quadrilateral_area(self) -> float:
        ordered_points = (
            self.nut_string6,
            self.high_fret_string6,
            self.high_fret_string1,
            self.nut_string1,
        )
        total = 0.0
        for index, point in enumerate(ordered_points):
            next_point = ordered_points[(index + 1) % len(ordered_points)]
            total += (point.x * next_point.y) - (next_point.x * point.y)
        return total / 2.0


def _interpolate(start: ImagePoint, end: ImagePoint, amount: float) -> ImagePoint:
    return ImagePoint(
        x=start.x + ((end.x - start.x) * amount),
        y=start.y + ((end.y - start.y) * amount),
    )


def _subtract(left: ImagePoint, right: ImagePoint) -> ImagePoint:
    return ImagePoint(x=left.x - right.x, y=left.y - right.y)


__all__ = [
    "ImagePoint",
    "ManualFretboardCalibration",
    "NormalizedFretboardPoint",
    "REQUIRED_POINT_NAMES",
]
