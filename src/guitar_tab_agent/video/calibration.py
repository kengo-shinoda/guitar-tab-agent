"""Manual fretboard calibration data structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImagePoint:
    """A point in image coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class FretboardCalibration:
    """Minimal manual calibration placeholder for future video fusion."""

    low_string_bridge: ImagePoint
    high_string_bridge: ImagePoint
    low_string_nut: ImagePoint
    high_string_nut: ImagePoint
