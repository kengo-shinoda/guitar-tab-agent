"""Video pipeline boundaries.

Real frame extraction, calibration, and landmark detection are future work.
"""

from guitar_tab_agent.video.fretboard_calibration import (
    ImagePoint,
    ManualFretboardCalibration,
    NormalizedFretboardPoint,
)

__all__ = [
    "ImagePoint",
    "ManualFretboardCalibration",
    "NormalizedFretboardPoint",
]
