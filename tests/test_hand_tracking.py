from pathlib import Path
from types import SimpleNamespace

import pytest

import guitar_tab_agent.video.hand_tracking as hand_tracking
from guitar_tab_agent.schema import HandLandmarkFrame
from guitar_tab_agent.video.hand_tracking import (
    MEDIAPIPE_HAND_LANDMARK_NAMES,
    MediaPipeUnavailableError,
    extract_hand_landmarks,
)


def test_missing_mediapipe_produces_readable_error(monkeypatch) -> None:
    def fake_import_module(name: str):
        raise ModuleNotFoundError("No module named 'mediapipe'", name="mediapipe")

    monkeypatch.setattr(hand_tracking, "import_module", fake_import_module)

    with pytest.raises(MediaPipeUnavailableError, match="MediaPipe is not installed"):
        extract_hand_landmarks(Path("frame.png"))


def test_mediapipe_is_loaded_lazily_for_frame_paths(monkeypatch) -> None:
    calls: list[str] = []

    class FakeHands:
        def __init__(self, **kwargs):
            assert kwargs == {"static_image_mode": True, "max_num_hands": 2}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def process(self, image):
            assert image == "loaded-frame.png"
            return SimpleNamespace(
                multi_hand_landmarks=[
                    SimpleNamespace(landmark=[SimpleNamespace(x=0.10, y=0.20)])
                ],
                multi_handedness=[],
            )

    fake_mediapipe = SimpleNamespace(
        Image=SimpleNamespace(
            create_from_file=lambda path: calls.append(path) or "loaded-frame.png"
        ),
        solutions=SimpleNamespace(hands=SimpleNamespace(Hands=FakeHands)),
    )
    monkeypatch.setattr(
        hand_tracking,
        "import_module",
        lambda name: fake_mediapipe,
    )

    frame = extract_hand_landmarks(Path("frame.png"))

    assert calls == ["frame.png"]
    assert frame.landmarks == (("wrist", 0.10, 0.20),)


def test_tasks_api_requires_model_path_when_legacy_api_is_unavailable(
    monkeypatch,
) -> None:
    fake_mediapipe = SimpleNamespace(
        Image=SimpleNamespace(create_from_file=lambda path: "loaded-frame.png"),
        solutions=None,
        tasks=SimpleNamespace(
            BaseOptions=lambda **kwargs: SimpleNamespace(**kwargs),
            vision=SimpleNamespace(
                HandLandmarker=SimpleNamespace(create_from_options=lambda options: None),
                HandLandmarkerOptions=lambda **kwargs: SimpleNamespace(**kwargs),
            ),
        ),
    )
    monkeypatch.setattr(
        hand_tracking,
        "import_module",
        lambda name: fake_mediapipe,
    )

    with pytest.raises(MediaPipeUnavailableError, match=r"\.task` model path"):
        extract_hand_landmarks(Path("frame.png"))


def test_tasks_api_path_converts_to_hand_landmark_frame(monkeypatch) -> None:
    calls: list[str] = []
    options_seen: list[object] = []

    class FakeTaskLandmarker:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def detect(self, image):
            assert image == "loaded-frame.png"
            return SimpleNamespace(
                hand_landmarks=[
                    [
                        SimpleNamespace(x=0.10, y=0.20),
                        SimpleNamespace(x=0.30, y=0.40),
                    ]
                ],
                handedness=[
                    [
                        SimpleNamespace(category_name="Left", score=0.85),
                    ]
                ],
            )

    class FakeHandLandmarker:
        @staticmethod
        def create_from_options(options):
            options_seen.append(options)
            return FakeTaskLandmarker()

    fake_mediapipe = SimpleNamespace(
        Image=SimpleNamespace(
            create_from_file=lambda path: calls.append(path) or "loaded-frame.png"
        ),
        solutions=None,
        tasks=SimpleNamespace(
            BaseOptions=lambda **kwargs: SimpleNamespace(**kwargs),
            vision=SimpleNamespace(
                HandLandmarker=FakeHandLandmarker,
                HandLandmarkerOptions=lambda **kwargs: SimpleNamespace(**kwargs),
                RunningMode=SimpleNamespace(IMAGE="IMAGE"),
            ),
        ),
    )
    monkeypatch.setattr(
        hand_tracking,
        "import_module",
        lambda name: fake_mediapipe,
    )

    frame = extract_hand_landmarks(
        Path("frame.png"),
        timestamp=1.25,
        mediapipe_model=Path("hand_landmarker.task"),
    )

    assert calls == ["frame.png"]
    assert options_seen[0].base_options.model_asset_path == "hand_landmarker.task"
    assert options_seen[0].num_hands == 2
    assert options_seen[0].running_mode == "IMAGE"
    assert frame == HandLandmarkFrame(
        timestamp=1.25,
        landmarks=(
            ("left:wrist", 0.10, 0.20),
            ("left:thumb_cmc", 0.30, 0.40),
        ),
        confidence=0.85,
    )


def test_model_path_selects_tasks_api_even_when_legacy_api_exists(monkeypatch) -> None:
    class FakeHands:
        def __init__(self, **kwargs):
            raise AssertionError("legacy API should not be used with a model path")

    class FakeTaskLandmarker:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def detect(self, image):
            return SimpleNamespace(
                hand_landmarks=[[SimpleNamespace(x=0.10, y=0.20)]],
                handedness=[],
            )

    class FakeHandLandmarker:
        @staticmethod
        def create_from_options(options):
            return FakeTaskLandmarker()

    fake_mediapipe = SimpleNamespace(
        Image=SimpleNamespace(create_from_file=lambda path: "loaded-frame.png"),
        solutions=SimpleNamespace(hands=SimpleNamespace(Hands=FakeHands)),
        tasks=SimpleNamespace(
            BaseOptions=lambda **kwargs: SimpleNamespace(**kwargs),
            vision=SimpleNamespace(
                HandLandmarker=FakeHandLandmarker,
                HandLandmarkerOptions=lambda **kwargs: SimpleNamespace(**kwargs),
            ),
        ),
    )
    monkeypatch.setattr(
        hand_tracking,
        "import_module",
        lambda name: fake_mediapipe,
    )

    frame = extract_hand_landmarks(
        Path("frame.png"),
        mediapipe_model=Path("hand_landmarker.task"),
    )

    assert frame.landmarks == (("wrist", 0.10, 0.20),)


def test_mocked_mediapipe_output_converts_to_hand_landmark_frame(monkeypatch) -> None:
    result = SimpleNamespace(
        multi_hand_landmarks=[
            SimpleNamespace(
                landmark=[
                    SimpleNamespace(x=0.10, y=0.20),
                    SimpleNamespace(x=0.30, y=0.40),
                ]
            )
        ],
        multi_handedness=[
            SimpleNamespace(
                classification=[
                    SimpleNamespace(label="Left", score=0.85),
                ]
            )
        ],
    )
    monkeypatch.setattr(
        hand_tracking,
        "_detect_hands_with_mediapipe",
        lambda frame_path_or_image: result,
    )

    frame = extract_hand_landmarks("frame.png", timestamp=1.25)

    assert frame == HandLandmarkFrame(
        timestamp=1.25,
        landmarks=(
            ("left:wrist", 0.10, 0.20),
            ("left:thumb_cmc", 0.30, 0.40),
        ),
        confidence=0.85,
    )


def test_landmark_order_and_count_are_stable(monkeypatch) -> None:
    landmarks = [
        SimpleNamespace(x=index / 100.0, y=(index + 1) / 100.0)
        for index in range(len(MEDIAPIPE_HAND_LANDMARK_NAMES))
    ]
    result = SimpleNamespace(
        multi_hand_landmarks=[SimpleNamespace(landmark=landmarks)],
        multi_handedness=[
            SimpleNamespace(
                classification=[
                    SimpleNamespace(label="Right", score=0.75),
                ]
            )
        ],
    )
    monkeypatch.setattr(
        hand_tracking,
        "_detect_hands_with_mediapipe",
        lambda frame_path_or_image: result,
    )

    frame = extract_hand_landmarks(object())

    assert len(frame.landmarks) == 21
    assert [landmark[0] for landmark in frame.landmarks] == [
        f"right:{name}" for name in MEDIAPIPE_HAND_LANDMARK_NAMES
    ]
    assert frame.landmarks[0] == ("right:wrist", 0.0, 0.01)
    assert frame.landmarks[-1] == ("right:pinky_tip", 0.20, 0.21)


def test_selects_requested_hand_index(monkeypatch) -> None:
    result = SimpleNamespace(
        multi_hand_landmarks=[
            SimpleNamespace(landmark=[SimpleNamespace(x=0.10, y=0.20)]),
            SimpleNamespace(landmark=[SimpleNamespace(x=0.70, y=0.80)]),
        ],
        multi_handedness=[
            SimpleNamespace(
                classification=[
                    SimpleNamespace(label="Left", score=0.50),
                ]
            ),
            SimpleNamespace(
                classification=[
                    SimpleNamespace(label="Right", score=0.90),
                ]
            ),
        ],
    )
    monkeypatch.setattr(
        hand_tracking,
        "_detect_hands_with_mediapipe",
        lambda frame_path_or_image: result,
    )

    frame = extract_hand_landmarks("frame.png", hand_index=1)

    assert frame.landmarks == (("right:wrist", 0.70, 0.80),)
    assert frame.confidence == 0.90


def test_no_detected_hand_returns_empty_frame(monkeypatch) -> None:
    result = SimpleNamespace(multi_hand_landmarks=[], multi_handedness=[])
    monkeypatch.setattr(
        hand_tracking,
        "_detect_hands_with_mediapipe",
        lambda frame_path_or_image: result,
    )

    frame = extract_hand_landmarks("frame.png", timestamp=0.5)

    assert frame == HandLandmarkFrame(timestamp=0.5, landmarks=(), confidence=None)


def test_negative_hand_index_is_rejected() -> None:
    with pytest.raises(ValueError, match="hand_index must be non-negative"):
        extract_hand_landmarks("frame.png", hand_index=-1)
