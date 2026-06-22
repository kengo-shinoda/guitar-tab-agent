"""Audio pipeline boundaries.

Real extraction and transcription will be added after the repository skeleton.
"""

from guitar_tab_agent.audio.basic_pitch_adapter import (
    BasicPitchUnavailableError,
    transcribe_audio_to_notes,
)
from guitar_tab_agent.audio.note_filtering import (
    filter_note_events,
    validate_note_filter_thresholds,
)

__all__ = [
    "BasicPitchUnavailableError",
    "filter_note_events",
    "transcribe_audio_to_notes",
    "validate_note_filter_thresholds",
]
