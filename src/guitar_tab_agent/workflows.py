"""Reusable local-first workflow functions.

The CLI should remain a thin wrapper around these functions. Future local API,
web UI, desktop, or optional cloud layers should call the same workflows instead
of duplicating decoder and renderer logic.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from guitar_tab_agent.audio.basic_pitch_adapter import transcribe_audio_to_notes
from guitar_tab_agent.audio.note_filtering import (
    filter_note_events,
    select_single_note_by_onset,
    sort_note_events_chronologically,
    validate_note_filter_thresholds,
)
from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    FingeringPosition,
    LeftHandFretLikelihoodByTime,
    decode_audio_notes,
    decode_audio_notes_top_k,
)
from guitar_tab_agent.schema import (
    DecodedTabEvent,
    FretboardCalibration,
    HandLandmarkFrame,
    NoteEvent,
)
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab
from guitar_tab_agent.video.frame_list_json import FrameImageRecord
from guitar_tab_agent.video.fretboard_transform import (
    transform_hand_landmark_frames_to_fretboard,
)
from guitar_tab_agent.video.hand_tracking import extract_hand_landmarks
from guitar_tab_agent.video.left_hand_likelihood import (
    DEFAULT_MAX_FRET,
    estimate_left_hand_fret_likelihood,
)


LandmarkExtractor = Callable[..., HandLandmarkFrame]
NoteTranscriber = Callable[[Path], Sequence[NoteEvent]]


@dataclass(frozen=True)
class RenderedTabCandidate:
    """Rendered TAB candidate with ranking metadata."""

    rank: int
    score: float
    tab: str
    events: tuple[DecodedTabEvent, ...]


def transcribe_audio_file_to_notes(
    audio_path: Path,
    *,
    min_confidence: float | None = None,
    min_duration: float | None = None,
    min_pitch: int | None = None,
    max_pitch: int | None = None,
    single_note: bool = False,
    transcriber: NoteTranscriber = transcribe_audio_to_notes,
) -> list[NoteEvent]:
    """Transcribe an audio file, apply optional filters, and sort notes."""

    validate_note_filter_thresholds(
        min_confidence=min_confidence,
        min_duration=min_duration,
        min_pitch=min_pitch,
        max_pitch=max_pitch,
    )
    notes = sort_note_events_chronologically(
        filter_note_events(
            transcriber(audio_path),
            min_confidence=min_confidence,
            min_duration=min_duration,
            min_pitch=min_pitch,
            max_pitch=max_pitch,
        )
    )
    if single_note:
        return select_single_note_by_onset(notes)
    return notes


def transcribe_audio_file_to_ascii_tab(
    audio_path: Path,
    *,
    min_confidence: float | None = None,
    min_duration: float | None = None,
    min_pitch: int | None = None,
    max_pitch: int | None = None,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
    single_note: bool = False,
    transcriber: NoteTranscriber = transcribe_audio_to_notes,
) -> str:
    """Run the current audio-only transcription-to-TAB workflow."""

    notes = transcribe_audio_file_to_notes(
        audio_path,
        min_confidence=min_confidence,
        min_duration=min_duration,
        min_pitch=min_pitch,
        max_pitch=max_pitch,
        single_note=single_note,
        transcriber=transcriber,
    )
    return render_notes_to_ascii_tab(
        notes,
        left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
        left_hand_weight=left_hand_weight,
        first_position=first_position,
    )


def transcribe_audio_file_to_ascii_tab_candidates(
    audio_path: Path,
    *,
    top_k: int,
    min_confidence: float | None = None,
    min_duration: float | None = None,
    min_pitch: int | None = None,
    max_pitch: int | None = None,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
    single_note: bool = False,
    transcriber: NoteTranscriber = transcribe_audio_to_notes,
) -> tuple[RenderedTabCandidate, ...]:
    """Run the audio-to-TAB workflow and render multiple candidate paths."""

    notes = transcribe_audio_file_to_notes(
        audio_path,
        min_confidence=min_confidence,
        min_duration=min_duration,
        min_pitch=min_pitch,
        max_pitch=max_pitch,
        single_note=single_note,
        transcriber=transcriber,
    )
    return render_notes_to_ascii_tab_candidates(
        notes,
        top_k=top_k,
        left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
        left_hand_weight=left_hand_weight,
        first_position=first_position,
    )


def render_notes_to_ascii_tab(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
) -> str:
    """Decode notes and render ASCII TAB.

    Left-hand likelihood evidence is optional and keyed by note start time. Fret
    likelihoods are evidence over frets `1..max_fret`; open strings receive
    neutral evidence in the decoder. This workflow is not full video end-to-end
    transcription.
    """

    sorted_notes = sort_note_events_chronologically(notes)
    return render_ascii_tab(
        decode_audio_notes(
            sorted_notes,
            left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
            left_hand_weight=left_hand_weight,
            first_position=first_position,
        )
    )


def render_notes_to_ascii_tab_candidates(
    notes: Sequence[NoteEvent],
    *,
    top_k: int,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    first_position: FingeringPosition | None = None,
) -> tuple[RenderedTabCandidate, ...]:
    """Decode and render multiple ranked ASCII TAB candidates."""

    sorted_notes = sort_note_events_chronologically(notes)
    decoded_candidates = decode_audio_notes_top_k(
        sorted_notes,
        top_k=top_k,
        left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
        left_hand_weight=left_hand_weight,
        first_position=first_position,
    )
    return tuple(
        RenderedTabCandidate(
            rank=candidate.rank,
            score=candidate.total_score,
            tab=render_ascii_tab(candidate.events),
            events=candidate.events,
        )
        for candidate in decoded_candidates
    )


def format_rendered_tab_candidates(
    candidates: Sequence[RenderedTabCandidate],
) -> str:
    """Format ranked TAB candidates as labeled plain-text blocks."""

    return "\n\n".join(
        f"Candidate {candidate.rank} score={candidate.score:.3f}\n{candidate.tab}"
        for candidate in candidates
    )


def hand_landmark_frames_to_left_hand_likelihood_records(
    frames: Sequence[HandLandmarkFrame],
    *,
    max_fret: int = DEFAULT_MAX_FRET,
) -> list[dict[str, object]]:
    """Convert hand landmark frames to left-hand likelihood JSON records."""

    if max_fret <= 0:
        raise ValueError("max_fret must be positive")

    records: list[dict[str, object]] = []
    for frame in frames:
        likelihood = estimate_left_hand_fret_likelihood(frame, max_fret=max_fret)
        records.append(
            {
                "time": frame.timestamp,
                "likelihood": {
                    str(fret): score for fret, score in sorted(likelihood.items())
                },
            }
        )
    return records


def hand_landmark_frames_to_left_hand_likelihood_json(
    frames: Sequence[HandLandmarkFrame],
    *,
    max_fret: int = DEFAULT_MAX_FRET,
) -> str:
    """Serialize frames as left-hand likelihood JSON."""

    return json.dumps(
        hand_landmark_frames_to_left_hand_likelihood_records(
            frames,
            max_fret=max_fret,
        ),
        indent=2,
    )


def frame_images_to_hand_landmark_frames(
    frames: Sequence[FrameImageRecord],
    *,
    hand_index: int = 0,
    mediapipe_model: str | Path | None = None,
    extractor: LandmarkExtractor = extract_hand_landmarks,
) -> list[HandLandmarkFrame]:
    """Extract hand landmarks from ordered frame images.

    The default extractor is the optional MediaPipe adapter. Tests and future
    workflow layers can inject a fake extractor without requiring MediaPipe or
    real images.
    """

    if hand_index < 0:
        raise ValueError("hand_index must be non-negative")

    landmark_frames: list[HandLandmarkFrame] = []
    for frame in frames:
        kwargs: dict[str, object] = {
            "timestamp": frame.timestamp,
            "hand_index": hand_index,
        }
        if mediapipe_model is not None:
            kwargs["mediapipe_model"] = mediapipe_model
        landmark_frames.append(extractor(frame.path, **kwargs))
    return landmark_frames


def hand_landmark_frames_to_json(frames: Sequence[HandLandmarkFrame]) -> str:
    """Serialize `HandLandmarkFrame` records as deterministic JSON."""

    return json.dumps(
        [
            {
                "timestamp": frame.timestamp,
                "landmarks": [
                    [name, x, y] for name, x, y in frame.landmarks
                ],
                "confidence": frame.confidence,
            }
            for frame in frames
        ],
        indent=2,
    )


def calibrate_hand_landmark_frames_to_json(
    frames: Sequence[HandLandmarkFrame],
    calibration: FretboardCalibration,
) -> str:
    """Transform image-space landmarks and serialize calibrated frames."""

    return hand_landmark_frames_to_json(
        transform_hand_landmark_frames_to_fretboard(list(frames), calibration)
    )


__all__ = [
    "LandmarkExtractor",
    "NoteTranscriber",
    "RenderedTabCandidate",
    "calibrate_hand_landmark_frames_to_json",
    "format_rendered_tab_candidates",
    "frame_images_to_hand_landmark_frames",
    "hand_landmark_frames_to_json",
    "hand_landmark_frames_to_left_hand_likelihood_json",
    "hand_landmark_frames_to_left_hand_likelihood_records",
    "render_notes_to_ascii_tab",
    "render_notes_to_ascii_tab_candidates",
    "transcribe_audio_file_to_ascii_tab_candidates",
    "transcribe_audio_file_to_ascii_tab",
    "transcribe_audio_file_to_notes",
]
