import pytest

from guitar_tab_agent.models import TabEvent, TabPosition
from guitar_tab_agent.schema import (
    DecodedTabEvent,
    FretboardCalibration,
    HandLandmarkFrame,
    NoteEvent,
    StringFretCandidate,
)


def test_note_event_construction_and_compatibility_aliases() -> None:
    event = NoteEvent(
        start=1.0,
        end=1.5,
        pitch_midi=64,
        confidence=0.75,
        source="fixture",
    )

    assert event.start == 1.0
    assert event.onset == 1.0
    assert event.duration == 0.5
    assert event.pitch_midi == 64
    assert event.midi_pitch == 64


def test_note_event_rejects_invalid_time_range() -> None:
    with pytest.raises(ValueError, match="end"):
        NoteEvent(start=2.0, end=1.0, pitch_midi=64, confidence=1.0)


def test_note_event_rejects_invalid_pitch() -> None:
    with pytest.raises(ValueError, match="pitch_midi"):
        NoteEvent(start=0.0, end=1.0, pitch_midi=128, confidence=1.0)


def test_string_fret_candidate_validation_and_aliases() -> None:
    candidate = StringFretCandidate(
        string=2,
        fret=5,
        pitch_midi=64,
        confidence=None,
    )

    assert candidate.string_number == 2
    assert candidate.fret_number == 5


def test_string_fret_candidate_rejects_invalid_string() -> None:
    with pytest.raises(ValueError, match="string"):
        StringFretCandidate(string=7, fret=0, pitch_midi=64)


def test_decoded_tab_event_validation() -> None:
    event = DecodedTabEvent(
        start=0.0,
        end=0.25,
        string=1,
        fret=0,
        pitch_midi=64,
        confidence=1.0,
    )

    assert event.string == 1
    assert event.fret == 0


def test_decoded_tab_event_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        DecodedTabEvent(
            start=0.0,
            end=0.25,
            string=1,
            fret=0,
            pitch_midi=64,
            confidence=1.5,
        )


def test_placeholder_video_schemas_are_constructible() -> None:
    calibration = FretboardCalibration(
        nut_string_6=(0.0, 0.0),
        nut_string_1=(0.0, 1.0),
        bridge_string_6=(1.0, 0.0),
        bridge_string_1=(1.0, 1.0),
        timestamp=0.0,
    )
    frame = HandLandmarkFrame(
        timestamp=0.25,
        landmarks=(("index_tip", 0.5, 0.5),),
        confidence=0.9,
    )

    assert calibration.nut_string_6 == (0.0, 0.0)
    assert frame.landmarks[0][0] == "index_tip"


def test_hand_landmark_frame_rejects_empty_landmark_name() -> None:
    with pytest.raises(ValueError, match="name"):
        HandLandmarkFrame(timestamp=0.25, landmarks=(("", 0.5, 0.5),))


def test_backward_compatible_tab_wrappers() -> None:
    note = NoteEvent(start=0.0, end=0.25, pitch_midi=64, confidence=1.0)
    position = TabPosition(string_number=1, fret_number=0)
    event = TabEvent(note=note, position=position)

    assert event.position is not None
    assert event.position.string == 1
    assert position.to_candidate(pitch_midi=64).fret == 0
