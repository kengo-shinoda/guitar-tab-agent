"""Left-hand fret likelihood from normalized fingertip landmarks.

This module prepares video evidence for future decoder integration. It assumes
input landmarks are already expressed in normalized fretboard coordinates:

- `u` runs from nut toward bridge/high-fret direction.
- `v` runs from the string 6 side toward the string 1 side.
- Points inside the calibrated fretboard region are approximately in
  `[0, 1] x [0, 1]`.

The MVP only uses fingertip landmarks and approximates fretted regions by
dividing the normalized `u` axis evenly. Fret 0 is an open-string position, so
left-hand fingertip evidence scores only frets 1 through `max_fret`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from guitar_tab_agent.schema import HandLandmarkFrame, LandmarkPoint


DEFAULT_MAX_FRET = 24
FINGERTIP_LANDMARK_NAMES = frozenset(
    {
        "index_finger_tip",
        "middle_finger_tip",
        "ring_finger_tip",
        "pinky_tip",
    }
)

FretLikelihood = dict[int, float]


def estimate_left_hand_fret_likelihood(
    landmarks_or_frame: HandLandmarkFrame | Sequence[LandmarkPoint],
    *,
    max_fret: int = DEFAULT_MAX_FRET,
) -> FretLikelihood:
    """Estimate deterministic likelihood-like scores over fretted regions.

    The returned mapping uses fret numbers as keys and non-negative scores as
    values. Scores are not probabilities; they are deterministic evidence values
    intended for later decoder consumption. Missing fingertips and
    out-of-fretboard fingertips produce an empty mapping.

    Hand labels are optional. Names such as `left:index_finger_tip` and
    `index_finger_tip` are treated equivalently.
    """

    if max_fret <= 0:
        raise ValueError("max_fret must be positive")

    fingertip_points = list(_iter_fingertip_points(landmarks_or_frame))
    if not fingertip_points:
        return {}

    fret_width = 1.0 / max_fret
    sigma = fret_width / 2.0
    scores: FretLikelihood = {fret: 0.0 for fret in range(1, max_fret + 1)}

    for u, _v in fingertip_points:
        for fret in range(1, max_fret + 1):
            center = _fret_region_center(fret, max_fret=max_fret)
            score = math.exp(-0.5 * ((u - center) / sigma) ** 2)
            scores[fret] = max(scores[fret], score)

    return scores


def _iter_fingertip_points(
    landmarks_or_frame: HandLandmarkFrame | Sequence[LandmarkPoint],
) -> Sequence[tuple[float, float]]:
    landmarks = (
        landmarks_or_frame.landmarks
        if isinstance(landmarks_or_frame, HandLandmarkFrame)
        else landmarks_or_frame
    )

    points: list[tuple[float, float]] = []
    for name, u, v in landmarks:
        if _base_landmark_name(name) not in FINGERTIP_LANDMARK_NAMES:
            continue
        if not _is_inside_normalized_fretboard(u, v):
            continue
        points.append((u, v))
    return points


def _base_landmark_name(name: str) -> str:
    return name.split(":", maxsplit=1)[-1]


def _is_inside_normalized_fretboard(u: float, v: float) -> bool:
    return 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0


def _fret_region_center(fret: int, *, max_fret: int) -> float:
    return (fret - 0.5) / max_fret


__all__ = [
    "DEFAULT_MAX_FRET",
    "FINGERTIP_LANDMARK_NAMES",
    "FretLikelihood",
    "estimate_left_hand_fret_likelihood",
]
