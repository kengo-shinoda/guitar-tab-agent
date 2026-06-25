import json

import pytest

import guitar_tab_agent.workflows as workflows
from guitar_tab_agent.fusion.simple_decoder import FingeringPosition
from guitar_tab_agent.schema import DecodedTabEvent, HandLandmarkFrame, NoteEvent
from guitar_tab_agent.video.frame_list_json import FrameImageRecord
from guitar_tab_agent.video.hand_landmark_frame_json import (
    load_hand_landmark_frames_json,
)
from guitar_tab_agent.workflows import (
    format_rendered_tab_candidates,
    frame_images_to_hand_landmark_frames,
    hand_landmark_frames_to_json,
    hand_landmark_frames_to_left_hand_likelihood_json,
    hand_landmark_frames_to_left_hand_likelihood_records,
    render_notes_to_ascii_tab,
    render_notes_to_ascii_tab_candidates,
    transcribe_audio_file_to_ascii_tab,
    transcribe_audio_file_to_ascii_tab_candidates,
    transcribe_audio_file_to_notes,
)


def _center(fret: int, *, max_fret: int) -> float:
    return (fret - 0.5) / max_fret


def _note(index: int, pitch_midi: int) -> NoteEvent:
    start = index * 0.25
    return NoteEvent(
        start=start,
        end=start + 0.2,
        pitch_midi=pitch_midi,
        confidence=1.0,
        source="test",
    )


def test_render_notes_to_ascii_tab_sorts_reverse_order_smoke_phrase() -> None:
    midi_sequence = [
        73,
        74,
        75,
        76,
        68,
        69,
        70,
        71,
        64,
        65,
        66,
        67,
        59,
        60,
        61,
        62,
    ]
    chronological_notes = [
        _note(index, pitch_midi) for index, pitch_midi in enumerate(midi_sequence)
    ]
    reverse_notes = list(reversed(chronological_notes))

    expected_tab = "\n".join(
        [
            "e|9101112---------------------",
            "B|-------9101112--------------",
            "G|--------------9101112-------",
            "D|---------------------9101112",
            "A|----------------------------",
            "E|----------------------------",
        ]
    )

    assert render_notes_to_ascii_tab(reverse_notes) == expected_tab
    assert render_notes_to_ascii_tab(chronological_notes) == expected_tab


def test_render_notes_to_ascii_tab_sorts_notes_before_decoding(monkeypatch) -> None:
    captured_starts: list[float] = []

    def fake_decode_audio_notes(notes, **kwargs):
        captured_starts.extend(note.start for note in notes)
        return [
            DecodedTabEvent(
                start=0.0,
                end=0.25,
                string=1,
                fret=0,
                pitch_midi=64,
                confidence=1.0,
            )
        ]

    monkeypatch.setattr(workflows, "decode_audio_notes", fake_decode_audio_notes)

    render_notes_to_ascii_tab(
        [
            _note(2, 67),
            _note(0, 64),
            _note(1, 65),
        ]
    )

    assert captured_starts == [0.0, 0.25, 0.5]


def test_transcribe_audio_file_to_notes_filters_and_sorts(tmp_path) -> None:
    audio_path = tmp_path / "input.wav"
    audio_path.write_bytes(b"fake audio")

    def fake_transcriber(path):
        assert path == audio_path
        return [
            _note(2, 65),
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=0.4,
                source="test",
            ),
            _note(1, 32),
        ]

    notes = transcribe_audio_file_to_notes(
        audio_path,
        min_confidence=0.5,
        min_pitch=40,
        transcriber=fake_transcriber,
    )

    assert [(note.start, note.pitch_midi) for note in notes] == [(0.5, 65)]


def test_transcribe_audio_file_to_ascii_tab_reuses_audio_workflow(tmp_path) -> None:
    audio_path = tmp_path / "input.wav"
    audio_path.write_bytes(b"fake audio")

    def fake_transcriber(path):
        assert path == audio_path
        return [
            _note(1, 45),
            _note(0, 64),
        ]

    tab = transcribe_audio_file_to_ascii_tab(
        audio_path,
        transcriber=fake_transcriber,
    )

    assert tab == "e|0-\nB|--\nG|--\nD|--\nA|-0\nE|--"


def test_render_notes_to_ascii_tab_candidates_formats_ranked_blocks() -> None:
    notes = [
        _note(0, 66),
        _note(1, 67),
        _note(2, 68),
        _note(3, 69),
    ]

    candidates = render_notes_to_ascii_tab_candidates(notes, top_k=2)
    formatted = format_rendered_tab_candidates(candidates)

    assert len(candidates) == 2
    assert candidates[0].rank == 1
    assert candidates[0].score <= candidates[1].score
    assert formatted.startswith("Candidate 1 score=")
    assert "\n\nCandidate 2 score=" in formatted
    assert "e|" in formatted


def test_render_notes_to_ascii_tab_candidates_uses_first_position_hint() -> None:
    notes = [
        _note(0, 66),
        _note(1, 67),
        _note(2, 68),
        _note(3, 69),
    ]

    candidates = render_notes_to_ascii_tab_candidates(
        notes,
        top_k=2,
        first_position=FingeringPosition(string=2, fret=7),
    )

    assert candidates[0].events[0].string == 2
    assert candidates[0].events[0].fret == 7
    assert "B|7" in candidates[0].tab


def test_transcribe_audio_file_to_ascii_tab_candidates_uses_injected_transcriber(
    tmp_path,
) -> None:
    audio_path = tmp_path / "input.wav"
    audio_path.write_bytes(b"fake audio")

    def fake_transcriber(path):
        assert path == audio_path
        return [
            _note(0, 66),
            _note(1, 67),
            _note(2, 68),
            _note(3, 69),
        ]

    candidates = transcribe_audio_file_to_ascii_tab_candidates(
        audio_path,
        top_k=2,
        transcriber=fake_transcriber,
    )

    assert len(candidates) == 2
    assert candidates[0].tab != candidates[1].tab


def test_transcribe_audio_file_rejects_invalid_thresholds(tmp_path) -> None:
    with pytest.raises(ValueError, match="min_pitch"):
        transcribe_audio_file_to_notes(
            tmp_path / "input.wav",
            min_pitch=90,
            max_pitch=80,
            transcriber=lambda path: [],
        )


def test_hand_landmark_frames_convert_to_left_hand_likelihood_records() -> None:
    max_fret = 12
    frames = [
        HandLandmarkFrame(
            timestamp=1.23,
            landmarks=(
                ("left:index_finger_tip", _center(5, max_fret=max_fret), 0.52),
            ),
            confidence=0.9,
        )
    ]

    records = hand_landmark_frames_to_left_hand_likelihood_records(
        frames,
        max_fret=max_fret,
    )

    assert records[0]["time"] == 1.23
    likelihood = records[0]["likelihood"]
    assert isinstance(likelihood, dict)
    assert max(likelihood, key=likelihood.get) == "5"
    assert likelihood["5"] == pytest.approx(1.0)


def test_hand_landmark_conversion_ignores_right_hand_landmarks() -> None:
    max_fret = 12
    frame = HandLandmarkFrame(
        timestamp=0.0,
        landmarks=(("right:index_finger_tip", _center(5, max_fret=max_fret), 0.5),),
    )

    assert hand_landmark_frames_to_left_hand_likelihood_records(
        [frame],
        max_fret=max_fret,
    ) == [{"time": 0.0, "likelihood": {}}]


def test_hand_landmark_conversion_empty_for_missing_or_out_of_fretboard_fingertips() -> None:
    frames = [
        HandLandmarkFrame(timestamp=0.0, landmarks=()),
        HandLandmarkFrame(
            timestamp=0.5,
            landmarks=(("left:index_finger_tip", 1.2, 0.5),),
        ),
    ]

    assert hand_landmark_frames_to_left_hand_likelihood_records(frames) == [
        {"time": 0.0, "likelihood": {}},
        {"time": 0.5, "likelihood": {}},
    ]


def test_hand_landmark_conversion_json_is_deterministic() -> None:
    max_fret = 4
    frames = [
        HandLandmarkFrame(
            timestamp=0.0,
            landmarks=(("left:index_finger_tip", _center(2, max_fret=max_fret), 0.5),),
        )
    ]

    first = hand_landmark_frames_to_left_hand_likelihood_json(
        frames,
        max_fret=max_fret,
    )
    second = hand_landmark_frames_to_left_hand_likelihood_json(
        frames,
        max_fret=max_fret,
    )

    assert first == second
    assert list(json.loads(first)[0]["likelihood"].keys()) == ["1", "2", "3", "4"]


def test_hand_landmark_conversion_rejects_invalid_max_fret() -> None:
    with pytest.raises(ValueError, match="max_fret must be positive"):
        hand_landmark_frames_to_left_hand_likelihood_records([], max_fret=0)


def test_frame_images_to_hand_landmark_frames_uses_injected_extractor(tmp_path) -> None:
    calls: list[tuple[object, float, int]] = []
    frames = [
        FrameImageRecord(path=tmp_path / "frame_0001.png", timestamp=1.23),
        FrameImageRecord(path=tmp_path / "frame_0002.png", timestamp=1.27),
    ]

    def fake_extractor(frame_path, *, timestamp: float, hand_index: int):
        calls.append((frame_path, timestamp, hand_index))
        return HandLandmarkFrame(
            timestamp=timestamp,
            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
            confidence=0.9,
        )

    landmark_frames = frame_images_to_hand_landmark_frames(
        frames,
        hand_index=1,
        extractor=fake_extractor,
    )

    assert calls == [
        (tmp_path / "frame_0001.png", 1.23, 1),
        (tmp_path / "frame_0002.png", 1.27, 1),
    ]
    assert [frame.timestamp for frame in landmark_frames] == [1.23, 1.27]


def test_frame_images_to_hand_landmark_frames_passes_mediapipe_model(tmp_path) -> None:
    calls: list[tuple[object, float, int, object]] = []
    frames = [FrameImageRecord(path=tmp_path / "frame_0001.png", timestamp=1.23)]
    model_path = tmp_path / "hand_landmarker.task"

    def fake_extractor(
        frame_path,
        *,
        timestamp: float,
        hand_index: int,
        mediapipe_model,
    ):
        calls.append((frame_path, timestamp, hand_index, mediapipe_model))
        return HandLandmarkFrame(
            timestamp=timestamp,
            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
            confidence=0.9,
        )

    landmark_frames = frame_images_to_hand_landmark_frames(
        frames,
        hand_index=1,
        mediapipe_model=model_path,
        extractor=fake_extractor,
    )

    assert calls == [(tmp_path / "frame_0001.png", 1.23, 1, model_path)]
    assert landmark_frames[0].timestamp == 1.23


def test_frame_images_to_hand_landmark_frames_rejects_negative_hand_index() -> None:
    with pytest.raises(ValueError, match="hand_index must be non-negative"):
        frame_images_to_hand_landmark_frames([], hand_index=-1)


def test_hand_landmark_frames_to_json_round_trips_with_loader(tmp_path) -> None:
    frames = [
        HandLandmarkFrame(
            timestamp=1.23,
            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
            confidence=0.9,
        )
    ]
    output_path = tmp_path / "hand_landmarks.json"

    output_path.write_text(hand_landmark_frames_to_json(frames), encoding="utf-8")

    assert load_hand_landmark_frames_json(output_path) == frames
