"""Reusable local-first workflow functions.

The CLI should remain a thin wrapper around these functions. Future local API,
web UI, desktop, or optional cloud layers should call the same workflows instead
of duplicating decoder and renderer logic.
"""

from __future__ import annotations

from collections.abc import Sequence

from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    LeftHandFretLikelihoodByTime,
    decode_audio_notes,
)
from guitar_tab_agent.schema import NoteEvent
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab


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


__all__ = ["render_notes_to_ascii_tab"]
