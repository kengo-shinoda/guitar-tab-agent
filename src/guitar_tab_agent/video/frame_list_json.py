"""JSON loading for ordered frame image lists."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FrameImageRecord:
    """A frame image path with its media timestamp."""

    path: Path
    timestamp: float


def load_frame_image_records_json(path: str | Path) -> list[FrameImageRecord]:
    """Load frame image records from JSON.

    Relative frame paths are resolved relative to the parent directory of the
    frame-list JSON file. Input order is preserved.
    """

    json_path = Path(path)
    try:
        raw_records = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid frame list JSON in {json_path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(f"could not read frame list JSON {json_path}: {exc}") from exc

    if not isinstance(raw_records, list):
        raise ValueError(f"expected a JSON list of frame records in {json_path}")

    return [
        _frame_record_from_json(raw_record, base_dir=json_path.parent, index=index)
        for index, raw_record in enumerate(raw_records)
    ]


def _frame_record_from_json(
    raw_record: Any,
    *,
    base_dir: Path,
    index: int,
) -> FrameImageRecord:
    if not isinstance(raw_record, dict):
        raise ValueError(f"frame record at index {index} must be a JSON object")

    try:
        raw_path = raw_record["path"]
        raw_timestamp = raw_record["timestamp"]
    except KeyError as exc:
        raise ValueError(
            f"frame record at index {index} is missing {exc.args[0]}"
        ) from exc

    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"frame record at index {index} path must be a string")
    if not _is_number(raw_timestamp):
        raise ValueError(f"frame record at index {index} timestamp must be numeric")

    frame_path = Path(raw_path)
    if not frame_path.is_absolute():
        frame_path = base_dir / frame_path

    return FrameImageRecord(path=frame_path, timestamp=float(raw_timestamp))


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = ["FrameImageRecord", "load_frame_image_records_json"]
