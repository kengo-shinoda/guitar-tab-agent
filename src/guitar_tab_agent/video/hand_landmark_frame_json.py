"""JSON helpers for serialized HandLandmarkFrame records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from guitar_tab_agent.schema import HandLandmarkFrame


def load_hand_landmark_frames_json(path: str | Path) -> list[HandLandmarkFrame]:
    """Load serialized `HandLandmarkFrame` records from a JSON list."""

    json_path = Path(path)
    try:
        raw_frames = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid HandLandmarkFrame JSON in {json_path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"could not read HandLandmarkFrame JSON {json_path}: {exc}"
        ) from exc

    if not isinstance(raw_frames, list):
        raise ValueError(
            f"expected a JSON list of HandLandmarkFrame records in {json_path}"
        )

    frames: list[HandLandmarkFrame] = []
    for index, raw_frame in enumerate(raw_frames):
        if not isinstance(raw_frame, dict):
            raise ValueError(
                f"HandLandmarkFrame record at index {index} must be an object"
            )
        try:
            frames.append(_hand_landmark_frame_from_record(raw_frame))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid HandLandmarkFrame record at index {index}: {exc}"
            ) from exc

    return frames


def _hand_landmark_frame_from_record(record: dict[str, Any]) -> HandLandmarkFrame:
    landmarks = record.get("landmarks", ())
    if landmarks is None:
        landmarks = ()
    if not isinstance(landmarks, list | tuple):
        raise ValueError("landmarks must be a list")

    return HandLandmarkFrame(
        timestamp=record["timestamp"],
        landmarks=tuple(_landmark_tuple(landmark) for landmark in landmarks),
        confidence=record.get("confidence"),
    )


def _landmark_tuple(landmark: Any) -> tuple[str, float, float]:
    if not isinstance(landmark, list | tuple):
        raise ValueError("landmark must be a three-item [name, x, y] record")
    if len(landmark) != 3:
        raise ValueError("landmark must be a three-item [name, x, y] record")

    name, x, y = landmark
    if not isinstance(name, str):
        raise ValueError("landmark name must be a string")
    if not _is_number(x) or not _is_number(y):
        raise ValueError("landmark coordinates must be numbers")
    return (name, float(x), float(y))


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = ["load_hand_landmark_frames_json"]
