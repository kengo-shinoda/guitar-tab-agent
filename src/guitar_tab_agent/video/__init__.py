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
from guitar_tab_agent.video.hand_tracking import (
    MEDIAPIPE_HAND_LANDMARK_NAMES,
    MediaPipeUnavailableError,
    extract_hand_landmarks,
)

__all__ = [
    "FrameExtractionError",
    "FrameInfo",
    "ImagePoint",
    "MEDIAPIPE_HAND_LANDMARK_NAMES",
    "ManualFretboardCalibration",
    "MediaPipeUnavailableError",
    "NormalizedFretboardPoint",
    "extract_frames",
    "extract_hand_landmarks",
]
