"""Video pipeline boundaries.

Real frame extraction, calibration, and landmark detection are future work.
"""

from guitar_tab_agent.video.fretboard_calibration import (
    ImagePoint,
    ManualFretboardCalibration,
    NormalizedFretboardPoint,
)
from guitar_tab_agent.video.frame_extractor import (
    FrameExtractionError,
    FrameInfo,
    extract_frames,
)

__all__ = [
    "FrameExtractionError",
    "FrameInfo",
    "ImagePoint",
    "ManualFretboardCalibration",
    "NormalizedFretboardPoint",
    "extract_frames",
]
