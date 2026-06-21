"""Audio pipeline placeholders."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from guitar_tab_agent.models import NoteEvent


def extract_note_events(_media_path: Path) -> Sequence[NoteEvent]:
    """Return note events extracted from media.

    This boundary will later call ffmpeg and Basic Pitch. It is intentionally
    unimplemented in the repository foundation phase.
    """

    raise NotImplementedError("audio transcription is not implemented yet")
