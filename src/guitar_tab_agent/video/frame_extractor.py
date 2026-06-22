"""Lightweight video frame extraction using the system ffmpeg executable.

This module intentionally avoids Python video dependencies such as OpenCV,
MediaPipe, or ffmpeg-python. It only shells out to `ffmpeg` and records the
deterministic frame paths and timestamps needed by Phase 1 video utilities.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


FRAME_FILENAME_PATTERN = "frame_%06d.png"


class FrameExtractionError(RuntimeError):
    """Raised when frame extraction cannot be completed."""


@dataclass(frozen=True)
class FrameInfo:
    """Metadata for one extracted frame."""

    index: int
    path: Path
    timestamp: float


def extract_frames(
    video_path: str | Path,
    fps: float,
    output_dir: str | Path,
    *,
    ffmpeg_executable: str = "ffmpeg",
) -> list[FrameInfo]:
    """Extract frames from `video_path` at `fps` into `output_dir`.

    Frame filenames are deterministic: `frame_000001.png`,
    `frame_000002.png`, and so on. Returned timestamps are seconds from video
    start, calculated as `(frame_index - 1) / fps`.
    """

    if fps <= 0:
        raise ValueError("fps must be positive")

    video = Path(video_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    command = _build_ffmpeg_command(
        video_path=video,
        fps=fps,
        output_pattern=output / FRAME_FILENAME_PATTERN,
        ffmpeg_executable=ffmpeg_executable,
    )
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise FrameExtractionError(
            f"ffmpeg executable not found: {ffmpeg_executable}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        message = f"ffmpeg failed while extracting frames from {video}"
        if detail:
            message = f"{message}: {detail}"
        raise FrameExtractionError(message) from exc

    return _frame_infos(output, fps)


def _build_ffmpeg_command(
    *,
    video_path: Path,
    fps: float,
    output_pattern: Path,
    ffmpeg_executable: str,
) -> list[str]:
    return [
        ffmpeg_executable,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={_format_fps(fps)}",
        str(output_pattern),
    ]


def _frame_infos(output_dir: Path, fps: float) -> list[FrameInfo]:
    frames: list[FrameInfo] = []
    for index, path in enumerate(sorted(output_dir.glob("frame_*.png")), start=1):
        frames.append(
            FrameInfo(
                index=index,
                path=path,
                timestamp=(index - 1) / fps,
            )
        )
    return frames


def _format_fps(fps: float) -> str:
    return str(int(fps)) if float(fps).is_integer() else str(fps)


__all__: Sequence[str] = [
    "FRAME_FILENAME_PATTERN",
    "FrameExtractionError",
    "FrameInfo",
    "extract_frames",
]
