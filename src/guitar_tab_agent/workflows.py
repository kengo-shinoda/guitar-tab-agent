"""Reusable local-first workflow functions.

The CLI should remain a thin wrapper around these functions. Future local API,
web UI, desktop, or optional cloud layers should call the same workflows instead
of duplicating decoder and renderer logic.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    LeftHandFretLikelihoodByTime,
    decode_audio_notes,
)
from guitar_tab_agent.schema import HandLandmarkFrame, NoteEvent
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab
from guitar_tab_agent.video.left_hand_likelihood import (
    DEFAULT_MAX_FRET,
    estimate_left_hand_fret_likelihood,
)


def render_notes_to_ascii_tab(
    notes: Sequence[NoteEvent],
    *,
    left_hand_fret_likelihood_by_time: LeftHandFretLikelihoodByTime | None = None,
    left_hand_weight: float = DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
) -> str:
    """Decode notes and render ASCII TAB.

    Left-hand likelihood evidence is optional and keyed by note start time. Fret
    likelihoods are evidence over frets `1..max_fret`; open strings receive
    neutral evidence in the decoder. This workflow is not full video end-to-end
    transcription.
    """

    return render_ascii_tab(
        decode_audio_notes(
            notes,
            left_hand_fret_likelihood_by_time=left_hand_fret_likelihood_by_time,
            left_hand_weight=left_hand_weight,
        )
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


__all__ = [
    "hand_landmark_frames_to_left_hand_likelihood_json",
    "hand_landmark_frames_to_left_hand_likelihood_records",
    "render_notes_to_ascii_tab",
]
