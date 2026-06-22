"""Optional Basic Pitch adapter for project NoteEvent records.

Basic Pitch is intentionally not a required dependency. This module imports it
only when transcription is requested, then normalizes Basic Pitch-like note
events into the project's stable `NoteEvent` schema.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from guitar_tab_agent.schema import NoteEvent


SOURCE_NAME = "basic_pitch"


class BasicPitchUnavailableError(ImportError):
    """Raised when Basic Pitch is not installed."""


@dataclass(frozen=True)
class _RawNoteFields:
    start: float
    end: float
    pitch_midi: int
    confidence: float


def transcribe_audio_to_notes(audio_path: Path) -> list[NoteEvent]:
    """Transcribe `audio_path` with Basic Pitch and return project notes.

    Raises `BasicPitchUnavailableError` when the optional Basic Pitch package is
    unavailable. The returned list contains only `NoteEvent` records; Basic
    Pitch-specific structures stay inside this adapter.
    """

    note_events = _predict_basic_pitch(audio_path)
    return [_to_note_event(raw_note) for raw_note in note_events]


def _predict_basic_pitch(audio_path: Path) -> Iterable[Any]:
    try:
        inference = import_module("basic_pitch.inference")
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("basic_pitch"):
            raise BasicPitchUnavailableError(
                "Basic Pitch is not installed. Install the optional "
                "`basic-pitch` package to use audio transcription."
            ) from exc
        raise

    predict = getattr(inference, "predict", None)
    if predict is None:
        raise BasicPitchUnavailableError(
            "Basic Pitch is installed but `basic_pitch.inference.predict` "
            "is unavailable."
        )

    result = predict(str(audio_path))
    if isinstance(result, tuple) and len(result) >= 3:
        return result[2]

    note_events = getattr(result, "note_events", None)
    if note_events is not None:
        return note_events

    raise ValueError("Basic Pitch output did not include note events")


def _to_note_event(raw_note: Any) -> NoteEvent:
    fields = _raw_note_fields(raw_note)
    return NoteEvent(
        start=fields.start,
        end=fields.end,
        pitch_midi=fields.pitch_midi,
        confidence=fields.confidence,
        source=SOURCE_NAME,
    )


def _raw_note_fields(raw_note: Any) -> _RawNoteFields:
    if isinstance(raw_note, dict):
        return _RawNoteFields(
            start=_number(raw_note, "start_time_s", "start"),
            end=_number(raw_note, "end_time_s", "end"),
            pitch_midi=int(_number(raw_note, "pitch_midi", "pitch")),
            confidence=_number(raw_note, "confidence", "amplitude", "velocity"),
        )

    if isinstance(raw_note, tuple | list):
        if len(raw_note) < 4:
            raise ValueError(
                "Basic Pitch note tuple must contain start, end, pitch, "
                "and confidence/amplitude"
            )
        start, end, pitch_midi, confidence = raw_note[:4]
        return _RawNoteFields(
            start=float(start),
            end=float(end),
            pitch_midi=int(pitch_midi),
            confidence=float(confidence),
        )

    return _RawNoteFields(
        start=float(_attr(raw_note, "start_time_s", "start")),
        end=float(_attr(raw_note, "end_time_s", "end")),
        pitch_midi=int(_attr(raw_note, "pitch_midi", "pitch")),
        confidence=float(_attr(raw_note, "confidence", "amplitude", "velocity")),
    )


def _number(raw_note: dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in raw_note:
            value = raw_note[key]
            if not isinstance(value, int | float):
                raise ValueError(f"Basic Pitch note field `{key}` must be numeric")
            return float(value)
    raise ValueError(
        "Basic Pitch note is missing one of: " + ", ".join(f"`{key}`" for key in keys)
    )


def _attr(raw_note: Any, *names: str) -> Any:
    for name in names:
        if hasattr(raw_note, name):
            return getattr(raw_note, name)
    raise ValueError(
        "Basic Pitch note is missing one of: "
        + ", ".join(f"`{name}`" for name in names)
    )


__all__ = [
    "BasicPitchUnavailableError",
    "SOURCE_NAME",
    "transcribe_audio_to_notes",
]
