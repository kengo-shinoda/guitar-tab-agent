"""Optional MediaPipe hand landmark adapter.

MediaPipe is intentionally not a required dependency. This module imports it
only when landmark extraction is requested, then normalizes MediaPipe-like hand
landmarks into the project's stable `HandLandmarkFrame` schema.

Coordinate convention:
- Landmarks use normalized image coordinates.
- x increases rightward.
- y increases downward.
- Values are expected to be approximately in [0, 1] when landmarks are inside
  the frame.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from guitar_tab_agent.schema import HandLandmarkFrame, LandmarkPoint


MEDIAPIPE_HAND_LANDMARK_NAMES: tuple[str, ...] = (
    "wrist",
    "thumb_cmc",
    "thumb_mcp",
    "thumb_ip",
    "thumb_tip",
    "index_finger_mcp",
    "index_finger_pip",
    "index_finger_dip",
    "index_finger_tip",
    "middle_finger_mcp",
    "middle_finger_pip",
    "middle_finger_dip",
    "middle_finger_tip",
    "ring_finger_mcp",
    "ring_finger_pip",
    "ring_finger_dip",
    "ring_finger_tip",
    "pinky_mcp",
    "pinky_pip",
    "pinky_dip",
    "pinky_tip",
)


class MediaPipeUnavailableError(ImportError):
    """Raised when MediaPipe is not installed or cannot provide hand tracking."""


def extract_hand_landmarks(
    frame_path_or_image: str | Path | Any,
    *,
    timestamp: float = 0.0,
    hand_index: int = 0,
    mediapipe_model: str | Path | None = None,
) -> HandLandmarkFrame:
    """Extract one hand's landmarks from a frame.

    `frame_path_or_image` defines the adapter boundary and may be a frame path
    or an image-like object accepted by the installed MediaPipe API. The return
    value contains only project-level `(name, x, y)` tuples. MediaPipe-specific
    result objects stay inside this module.

    Raises `MediaPipeUnavailableError` when the optional MediaPipe package is
    unavailable. `hand_index` selects a detected hand from MediaPipe's stable
    result order.
    """

    if hand_index < 0:
        raise ValueError("hand_index must be non-negative")

    if mediapipe_model is None:
        result = _detect_hands_with_mediapipe(frame_path_or_image)
    else:
        result = _detect_hands_with_mediapipe(
            frame_path_or_image,
            mediapipe_model=mediapipe_model,
        )
    return _hand_landmark_frame_from_result(
        result,
        timestamp=timestamp,
        hand_index=hand_index,
    )


def _detect_hands_with_mediapipe(
    frame_path_or_image: str | Path | Any,
    *,
    mediapipe_model: str | Path | None = None,
) -> Any:
    mediapipe = _load_mediapipe()
    hands_api = getattr(getattr(mediapipe, "solutions", None), "hands", None)
    hands_factory = getattr(hands_api, "Hands", None)

    if mediapipe_model is not None:
        return _detect_hands_with_mediapipe_tasks(
            mediapipe,
            frame_path_or_image,
            model_path=mediapipe_model,
        )

    if hands_factory is not None:
        return _detect_hands_with_legacy_mediapipe(
            mediapipe,
            hands_factory,
            frame_path_or_image,
        )

    if _tasks_hand_landmarker_available(mediapipe):
        raise MediaPipeUnavailableError(
            "MediaPipe Tasks hand landmarker requires a `.task` model path. "
            "Pass --mediapipe-model /path/to/hand_landmarker.task."
        )

    raise MediaPipeUnavailableError(
        "MediaPipe is installed but neither `mediapipe.solutions.hands.Hands` "
        "nor the MediaPipe Tasks hand landmarker API is available."
    )


def _detect_hands_with_legacy_mediapipe(
    mediapipe: Any,
    hands_factory: Any,
    frame_path_or_image: str | Path | Any,
) -> Any:
    image = _load_mediapipe_image(mediapipe, frame_path_or_image)

    with hands_factory(static_image_mode=True, max_num_hands=2) as hands:
        return hands.process(image)


def _detect_hands_with_mediapipe_tasks(
    mediapipe: Any,
    frame_path_or_image: str | Path | Any,
    *,
    model_path: str | Path | None,
) -> Any:
    if model_path is None:
        raise MediaPipeUnavailableError(
            "MediaPipe Tasks hand landmarker requires a `.task` model path. "
            "Pass --mediapipe-model /path/to/hand_landmarker.task."
        )

    tasks = getattr(mediapipe, "tasks", None)
    vision = getattr(tasks, "vision", None)
    landmarker_factory = getattr(vision, "HandLandmarker", None)
    options_factory = getattr(vision, "HandLandmarkerOptions", None)
    base_options_factory = getattr(tasks, "BaseOptions", None)

    if (
        landmarker_factory is None
        or options_factory is None
        or base_options_factory is None
    ):
        raise MediaPipeUnavailableError(
            "MediaPipe is installed but the MediaPipe Tasks hand landmarker API "
            "is unavailable."
        )

    create_from_options = getattr(landmarker_factory, "create_from_options", None)
    if create_from_options is None:
        raise MediaPipeUnavailableError(
            "MediaPipe Tasks hand landmarker is unavailable because "
            "`HandLandmarker.create_from_options` is missing."
        )

    options_kwargs: dict[str, Any] = {
        "base_options": base_options_factory(model_asset_path=str(model_path)),
        "num_hands": 2,
    }
    running_mode = getattr(vision, "RunningMode", None)
    image_mode = getattr(running_mode, "IMAGE", None)
    if image_mode is not None:
        options_kwargs["running_mode"] = image_mode

    image = _load_mediapipe_image(mediapipe, frame_path_or_image)
    options = options_factory(**options_kwargs)
    with create_from_options(options) as landmarker:
        return landmarker.detect(image)


def _tasks_hand_landmarker_available(mediapipe: Any) -> bool:
    tasks = getattr(mediapipe, "tasks", None)
    vision = getattr(tasks, "vision", None)
    return (
        getattr(mediapipe, "Image", None) is not None
        and getattr(vision, "HandLandmarker", None) is not None
        and getattr(vision, "HandLandmarkerOptions", None) is not None
        and getattr(tasks, "BaseOptions", None) is not None
    )


def _load_mediapipe_image(
    mediapipe: Any,
    frame_path_or_image: str | Path | Any,
) -> Any:
    if not isinstance(frame_path_or_image, str | Path):
        return frame_path_or_image

    image_loader = getattr(
        getattr(mediapipe, "Image", None),
        "create_from_file",
        None,
    )
    if image_loader is None:
        raise MediaPipeUnavailableError(
            "MediaPipe is installed, but this adapter cannot load frame paths "
            "without `mediapipe.Image.create_from_file`."
        )
    return image_loader(str(frame_path_or_image))


def _load_mediapipe() -> Any:
    try:
        return import_module("mediapipe")
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("mediapipe"):
            raise MediaPipeUnavailableError(
                "MediaPipe is not installed. Install the optional `mediapipe` "
                "package to use hand tracking."
            ) from exc
        raise


def _hand_landmark_frame_from_result(
    result: Any,
    *,
    timestamp: float,
    hand_index: int,
) -> HandLandmarkFrame:
    hand_landmarks = _result_hand_landmarks(result)
    if hand_index >= len(hand_landmarks):
        return HandLandmarkFrame(timestamp=timestamp, landmarks=(), confidence=None)

    handedness = _result_handedness(result)
    label, confidence = _hand_label_and_confidence(handedness, hand_index)
    landmarks = tuple(
        _to_project_landmark(index, landmark, label=label)
        for index, landmark in enumerate(_landmark_points(hand_landmarks[hand_index]))
    )

    return HandLandmarkFrame(
        timestamp=timestamp,
        landmarks=landmarks,
        confidence=confidence,
    )


def _result_hand_landmarks(result: Any) -> list[Any]:
    hand_landmarks = getattr(result, "multi_hand_landmarks", None)
    if hand_landmarks is not None:
        return list(hand_landmarks)

    task_hand_landmarks = getattr(result, "hand_landmarks", None)
    if task_hand_landmarks is not None:
        return list(task_hand_landmarks)

    return []


def _result_handedness(result: Any) -> list[Any]:
    handedness = getattr(result, "multi_handedness", None)
    if handedness is not None:
        return list(handedness)

    task_handedness = getattr(result, "handedness", None)
    if task_handedness is not None:
        return list(task_handedness)

    return []


def _hand_label_and_confidence(
    handedness: list[Any],
    hand_index: int,
) -> tuple[str | None, float | None]:
    if hand_index >= len(handedness):
        return None, None

    classification = _first_classification(handedness[hand_index])
    if classification is None:
        return None, None

    label = getattr(classification, "label", None)
    if label is None:
        label = getattr(classification, "category_name", None)
    score = getattr(classification, "score", None)
    return _normalized_label(label), None if score is None else float(score)


def _first_classification(handedness: Any) -> Any | None:
    classification = getattr(handedness, "classification", None)
    if classification:
        return classification[0]

    if isinstance(handedness, list | tuple) and handedness:
        return handedness[0]

    return None


def _landmark_points(hand_landmarks: Any) -> list[Any]:
    landmarks = getattr(hand_landmarks, "landmark", None)
    if landmarks is not None:
        return list(landmarks)

    if isinstance(hand_landmarks, list | tuple):
        return list(hand_landmarks)

    raise ValueError("MediaPipe hand landmarks did not include landmark points")


def _to_project_landmark(
    index: int,
    landmark: Any,
    *,
    label: str | None,
) -> LandmarkPoint:
    name = (
        MEDIAPIPE_HAND_LANDMARK_NAMES[index]
        if index < len(MEDIAPIPE_HAND_LANDMARK_NAMES)
        else f"landmark_{index}"
    )
    if label:
        name = f"{label}:{name}"

    return (name, float(getattr(landmark, "x")), float(getattr(landmark, "y")))


def _normalized_label(label: Any) -> str | None:
    if label is None:
        return None
    text = str(label).strip().lower()
    return text or None


__all__ = [
    "MEDIAPIPE_HAND_LANDMARK_NAMES",
    "MediaPipeUnavailableError",
    "extract_hand_landmarks",
]
