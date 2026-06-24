import json
from pathlib import Path

import pytest

from guitar_tab_agent.video.frame_list_json import (
    FrameImageRecord,
    load_frame_image_records_json,
)


def test_load_frame_image_records_json_resolves_relative_paths(tmp_path) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    frames_json = frames_dir / "frames.json"
    frames_json.write_text(
        json.dumps(
            [
                {"path": "frame_0001.png", "timestamp": 1.23},
                {"path": str(tmp_path / "absolute.png"), "timestamp": 1.27},
            ]
        ),
        encoding="utf-8",
    )

    records = load_frame_image_records_json(frames_json)

    assert records == [
        FrameImageRecord(path=frames_dir / "frame_0001.png", timestamp=1.23),
        FrameImageRecord(path=tmp_path / "absolute.png", timestamp=1.27),
    ]


def test_load_frame_image_records_json_rejects_invalid_json(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid frame list JSON"):
        load_frame_image_records_json(frames_json)


def test_load_frame_image_records_json_rejects_non_list_input(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text(json.dumps({"path": "frame.png"}), encoding="utf-8")

    with pytest.raises(ValueError, match="expected a JSON list"):
        load_frame_image_records_json(frames_json)


def test_load_frame_image_records_json_rejects_non_object_records(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text(json.dumps(["frame.png"]), encoding="utf-8")

    with pytest.raises(ValueError, match="frame record at index 0"):
        load_frame_image_records_json(frames_json)


def test_load_frame_image_records_json_rejects_missing_fields(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text(json.dumps([{"path": "frame.png"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="missing timestamp"):
        load_frame_image_records_json(frames_json)


def test_load_frame_image_records_json_rejects_invalid_field_types(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text(
        json.dumps([{"path": "frame.png", "timestamp": True}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="timestamp must be numeric"):
        load_frame_image_records_json(frames_json)


def test_load_frame_image_records_json_rejects_empty_path(tmp_path) -> None:
    frames_json = tmp_path / "frames.json"
    frames_json.write_text(
        json.dumps([{"path": "", "timestamp": 0.0}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="path must be a string"):
        load_frame_image_records_json(frames_json)
