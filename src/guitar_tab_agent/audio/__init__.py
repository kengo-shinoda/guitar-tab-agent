"""Audio pipeline boundaries.

Real extraction and transcription will be added after the repository skeleton.
"""

from guitar_tab_agent.audio.basic_pitch_adapter import (
    BasicPitchUnavailableError,
    transcribe_audio_to_notes,
)

__all__ = [
    "BasicPitchUnavailableError",
    "transcribe_audio_to_notes",
]
