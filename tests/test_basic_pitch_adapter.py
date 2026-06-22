from pathlib import Path
from types import SimpleNamespace

import pytest

import guitar_tab_agent.audio.basic_pitch_adapter as basic_pitch_adapter
from guitar_tab_agent.audio.basic_pitch_adapter import (
    BasicPitchUnavailableError,
    transcribe_audio_to_notes,
)
from guitar_tab_agent.schema import NoteEvent


def test_transcribe_audio_to_notes_normalizes_dict_output(monkeypatch) -> None:
    monkeypatch.setattr(
        basic_pitch_adapter,
        "_predict_basic_pitch",
        lambda audio_path: [
            {
                "start_time_s": 0.0,
                "end_time_s": 0.25,
                "pitch_midi": 64,
                "confidence": 0.9,
            },
            {
                "start_time_s": 0.5,
                "end_time_s": 0.75,
                "pitch_midi": 67,
                "amplitude": 0.8,
            },
        ],
    )

    notes = transcribe_audio_to_notes(Path("example.wav"))

    assert notes == [
        NoteEvent(
            start=0.0,
            end=0.25,
            pitch_midi=64,
            confidence=0.9,
            source="basic_pitch",
        ),
        NoteEvent(
            start=0.5,
            end=0.75,
            pitch_midi=67,
            confidence=0.8,
            source="basic_pitch",
        ),
    ]


def test_transcribe_audio_to_notes_normalizes_tuple_output(monkeypatch) -> None:
    monkeypatch.setattr(
        basic_pitch_adapter,
        "_predict_basic_pitch",
        lambda audio_path: [
            (1.0, 1.5, 69, 0.7),
        ],
    )

    notes = transcribe_audio_to_notes(Path("example.wav"))

    assert notes == [
        NoteEvent(
            start=1.0,
            end=1.5,
            pitch_midi=69,
            confidence=0.7,
            source="basic_pitch",
        )
    ]


def test_transcribe_audio_to_notes_normalizes_object_output(monkeypatch) -> None:
    monkeypatch.setattr(
        basic_pitch_adapter,
        "_predict_basic_pitch",
        lambda audio_path: [
            SimpleNamespace(
                start=2.0,
                end=2.25,
                pitch=72,
                velocity=0.6,
            )
        ],
    )

    notes = transcribe_audio_to_notes(Path("example.wav"))

    assert notes[0] == NoteEvent(
        start=2.0,
        end=2.25,
        pitch_midi=72,
        confidence=0.6,
        source="basic_pitch",
    )


def test_predict_basic_pitch_reads_note_events_from_predict_tuple(monkeypatch) -> None:
    captured_paths: list[str] = []

    def fake_predict(audio_path: str):
        captured_paths.append(audio_path)
        return "model-output", "midi-data", [(0.0, 0.25, 64, 0.9)]

    fake_inference = SimpleNamespace(predict=fake_predict)
    monkeypatch.setattr(
        basic_pitch_adapter,
        "import_module",
        lambda name: fake_inference,
    )

    notes = list(basic_pitch_adapter._predict_basic_pitch(Path("example.wav")))

    assert captured_paths == ["example.wav"]
    assert notes == [(0.0, 0.25, 64, 0.9)]


def test_missing_basic_pitch_produces_readable_error(monkeypatch) -> None:
    def fake_import_module(name: str):
        raise ModuleNotFoundError("No module named 'basic_pitch'", name="basic_pitch")

    monkeypatch.setattr(basic_pitch_adapter, "import_module", fake_import_module)

    with pytest.raises(BasicPitchUnavailableError, match="Basic Pitch is not installed"):
        transcribe_audio_to_notes(Path("example.wav"))


def test_invalid_basic_pitch_note_shape_is_readable(monkeypatch) -> None:
    monkeypatch.setattr(
        basic_pitch_adapter,
        "_predict_basic_pitch",
        lambda audio_path: [
            {"start_time_s": 0.0, "end_time_s": 0.25, "pitch_midi": 64},
        ],
    )

    with pytest.raises(ValueError, match="missing one of.*confidence"):
        transcribe_audio_to_notes(Path("example.wav"))
