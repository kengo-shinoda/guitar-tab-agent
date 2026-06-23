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
from guitar_tab_agent.video.left_hand_likelihood import (
    DEFAULT_MAX_FRET,
    FINGERTIP_LANDMARK_NAMES,
    FretLikelihood,
    estimate_left_hand_fret_likelihood,
)

__all__ = [
    "DEFAULT_MAX_FRET",
    "FINGERTIP_LANDMARK_NAMES",
    "FrameExtractionError",
    "FrameInfo",
    "FretLikelihood",
    "ImagePoint",
    "MEDIAPIPE_HAND_LANDMARK_NAMES",
    "ManualFretboardCalibration",
    "MediaPipeUnavailableError",
    "NormalizedFretboardPoint",
    "estimate_left_hand_fret_likelihood",
    "extract_frames",
    "extract_hand_landmarks",
]
