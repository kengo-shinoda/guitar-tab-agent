"""Canonical internal schemas for guitar-tab-agent."""

from __future__ import annotations

from dataclasses import dataclass


STANDARD_TUNING_MIDI: dict[int, int] = {
    1: 64,
    2: 59,
    3: 55,
    4: 50,
    5: 45,
    6: 40,
}

ImagePoint = tuple[float, float]
LandmarkPoint = tuple[str, float, float]

__all__ = [
    "STANDARD_TUNING_MIDI",
    "DecodedTabEvent",
    "FretboardCalibration",
    "HandLandmarkFrame",
    "ImagePoint",
    "LandmarkPoint",
    "NoteEvent",
    "StringFretCandidate",
    "validate_confidence",
    "validate_fret",
    "validate_image_point",
    "validate_landmark_point",
    "validate_midi_pitch",
    "validate_string_number",
    "validate_time_range",
    "validate_timestamp",
]


def validate_time_range(start: float, end: float) -> None:
    """Validate a media time range in seconds."""

    if start < 0:
        raise ValueError("start must be non-negative")
    if end < start:
        raise ValueError("end must be greater than or equal to start")


def validate_midi_pitch(pitch_midi: int) -> None:
    """Validate a MIDI pitch value."""

    if not 0 <= pitch_midi <= 127:
        raise ValueError("pitch_midi must be in the MIDI range 0..127")


def validate_confidence(confidence: float | None, *, allow_none: bool = False) -> None:
    """Validate a normalized confidence value."""

    if confidence is None:
        if allow_none:
            return
        raise ValueError("confidence must not be None")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")


def validate_string_number(string: int) -> None:
    """Validate a six-string guitar string number."""

    if string not in STANDARD_TUNING_MIDI:
        raise ValueError("string must be between 1 and 6")


def validate_fret(fret: int) -> None:
    """Validate a guitar fret number."""

    if fret < 0:
        raise ValueError("fret must be non-negative")


def validate_timestamp(timestamp: float | None) -> None:
    """Validate an optional media timestamp."""

    if timestamp is not None and timestamp < 0:
        raise ValueError("timestamp must be non-negative")


def validate_image_point(point: ImagePoint | None) -> None:
    """Validate an optional image-space point."""

    if point is None:
        return
    if len(point) != 2:
        raise ValueError("image point must contain x and y")


def validate_landmark_point(point: LandmarkPoint) -> None:
    """Validate a named project-level hand landmark point."""

    if len(point) != 3:
        raise ValueError("landmark point must contain name, x, and y")
    if not point[0]:
        raise ValueError("landmark point name must not be empty")


@dataclass(frozen=True)
class NoteEvent:
    """A normalized note event produced by an audio transcription stage."""

    start: float
    end: float
    pitch_midi: int
    confidence: float
    source: str = "unknown"

    def __post_init__(self) -> None:
        validate_time_range(self.start, self.end)
        validate_midi_pitch(self.pitch_midi)
        validate_confidence(self.confidence)
        if not self.source:
            raise ValueError("source must not be empty")

    @property
    def onset(self) -> float:
        """Backward-compatible alias for `start`."""

        return self.start

    @property
    def duration(self) -> float:
        """Backward-compatible duration derived from `start` and `end`."""

        return self.end - self.start

    @property
    def midi_pitch(self) -> int:
        """Backward-compatible alias for `pitch_midi`."""

        return self.pitch_midi


@dataclass(frozen=True)
class StringFretCandidate:
    """A playable string/fret candidate for a MIDI pitch."""

    string: int
    fret: int
    pitch_midi: int
    confidence: float | None = None

    def __post_init__(self) -> None:
        validate_string_number(self.string)
        validate_fret(self.fret)
        validate_midi_pitch(self.pitch_midi)
        validate_confidence(self.confidence, allow_none=True)

    @property
    def string_number(self) -> int:
        """Backward-compatible alias for `string`."""

        return self.string

    @property
    def fret_number(self) -> int:
        """Backward-compatible alias for `fret`."""

        return self.fret


@dataclass(frozen=True)
class DecodedTabEvent:
    """A decoded note placement in guitar TAB coordinates."""

    start: float
    end: float
    string: int
    fret: int
    pitch_midi: int
    confidence: float

    def __post_init__(self) -> None:
        validate_time_range(self.start, self.end)
        validate_string_number(self.string)
        validate_fret(self.fret)
        validate_midi_pitch(self.pitch_midi)
        validate_confidence(self.confidence)


@dataclass(frozen=True)
class FretboardCalibration:
    """Minimal placeholder for future manual fretboard calibration.

    Points are image-space `(x, y)` coordinates. No perspective transform or
    coordinate mapping is implemented in this schema layer.
    """

    nut_string_6: ImagePoint | None = None
    nut_string_1: ImagePoint | None = None
    bridge_string_6: ImagePoint | None = None
    bridge_string_1: ImagePoint | None = None
    timestamp: float | None = None

    def __post_init__(self) -> None:
        validate_image_point(self.nut_string_6)
        validate_image_point(self.nut_string_1)
        validate_image_point(self.bridge_string_6)
        validate_image_point(self.bridge_string_1)
        validate_timestamp(self.timestamp)


@dataclass(frozen=True)
class HandLandmarkFrame:
    """Minimal placeholder for future hand-tracking output.

    Landmarks are project-level `(name, x, y)` tuples. MediaPipe-specific
    objects must stay inside the video adapter layer.
    """

    timestamp: float
    landmarks: tuple[LandmarkPoint, ...] = ()
    confidence: float | None = None

    def __post_init__(self) -> None:
        validate_timestamp(self.timestamp)
        for landmark in self.landmarks:
            validate_landmark_point(landmark)
        validate_confidence(self.confidence, allow_none=True)
