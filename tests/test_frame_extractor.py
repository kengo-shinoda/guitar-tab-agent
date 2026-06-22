import subprocess
from pathlib import Path

import pytest

import guitar_tab_agent.video.frame_extractor as frame_extractor
from guitar_tab_agent.video.frame_extractor import (
    FRAME_FILENAME_PATTERN,
    FrameExtractionError,
    extract_frames,
)


def test_extract_frames_builds_expected_ffmpeg_command(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []
    video_path = tmp_path / "input.mp4"
    output_dir = tmp_path / "frames"

    def fake_run(command, **kwargs):
        calls.append(command)
        assert kwargs == {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(frame_extractor.subprocess, "run", fake_run)

    extract_frames(video_path, 2.0, output_dir)

    assert calls == [
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            "fps=2",
            str(output_dir / FRAME_FILENAME_PATTERN),
        ]
    ]
    assert output_dir.is_dir()


def test_extract_frames_returns_deterministic_paths_and_timestamps(
    monkeypatch,
    tmp_path,
) -> None:
    video_path = tmp_path / "input.mp4"
    output_dir = tmp_path / "frames"

    def fake_run(command, **kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "frame_000002.png").write_text("", encoding="utf-8")
        (output_dir / "frame_000001.png").write_text("", encoding="utf-8")
        (output_dir / "frame_000003.png").write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(frame_extractor.subprocess, "run", fake_run)

    frames = extract_frames(video_path, 2.0, output_dir)

    assert [frame.index for frame in frames] == [1, 2, 3]
    assert [frame.path for frame in frames] == [
        output_dir / "frame_000001.png",
        output_dir / "frame_000002.png",
        output_dir / "frame_000003.png",
    ]
    assert [frame.timestamp for frame in frames] == pytest.approx([0.0, 0.5, 1.0])


def test_extract_frames_keeps_fractional_fps_in_command(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(frame_extractor.subprocess, "run", fake_run)

    extract_frames(tmp_path / "input.mp4", 0.5, tmp_path / "frames")

    assert "fps=0.5" in calls[0]


def test_extract_frames_rejects_non_positive_fps(tmp_path) -> None:
    with pytest.raises(ValueError, match="fps must be positive"):
        extract_frames(tmp_path / "input.mp4", 0.0, tmp_path / "frames")


def test_extract_frames_reports_missing_ffmpeg(monkeypatch, tmp_path) -> None:
    def fake_run(command, **kwargs):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(frame_extractor.subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="ffmpeg executable not found"):
        extract_frames(tmp_path / "input.mp4", 1.0, tmp_path / "frames")


def test_extract_frames_reports_ffmpeg_failure(monkeypatch, tmp_path) -> None:
    def fake_run(command, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            stderr="invalid video",
        )

    monkeypatch.setattr(frame_extractor.subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="ffmpeg failed.*invalid video"):
        extract_frames(Path("missing.mp4"), 1.0, tmp_path / "frames")
