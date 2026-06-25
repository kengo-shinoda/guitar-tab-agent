import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import guitar_tab_agent.cli as cli
from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.cli import main
from guitar_tab_agent.schema import HandLandmarkFrame, NoteEvent
from guitar_tab_agent.video.hand_landmark_frame_json import (
    load_hand_landmark_frames_json,
)
from guitar_tab_agent.video.hand_tracking import MediaPipeUnavailableError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class CliTest(unittest.TestCase):
    def test_candidates_json(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["candidates", "64", "--max-fret", "0", "--json"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(output.getvalue()),
            [{"string": 1, "fret": 0, "pitch_midi": 64, "confidence": None}],
        )

    def test_no_command_prints_help(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("usage: tabgen", output.getvalue())

    def test_frames_to_landmarks_help(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as exc:
                main(["frames-to-landmarks", "--help"])

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("usage: tabgen frames-to-landmarks", output.getvalue())
        self.assertIn("--mediapipe-model", output.getvalue())

    def test_web_help(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as exc:
                main(["web", "--help"])

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("usage: tabgen web", output.getvalue())
        self.assertIn("--open-browser", output.getvalue())

    def test_notes_to_tab_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            notes_path = tmp_path / "notes.json"
            out_path = tmp_path / "tab.txt"
            notes_path.write_text(
                json.dumps(
                    [
                        {
                            "start": 0.0,
                            "end": 0.25,
                            "pitch_midi": 64,
                            "confidence": 1.0,
                            "source": "test",
                        },
                        {
                            "start": 0.5,
                            "end": 0.75,
                            "pitch_midi": 45,
                            "confidence": 0.9,
                            "source": "test",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            exit_code = main(["notes-to-tab", str(notes_path), "--out", str(out_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                out_path.read_text(encoding="utf-8"),
                "e|0--\nB|---\nG|---\nD|---\nA|--0\nE|---",
            )

    def test_notes_to_tab_prints_stdout_without_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            notes_path = Path(tmpdir) / "notes.json"
            notes_path.write_text(
                json.dumps(
                    [
                        {
                            "start": 0.0,
                            "end": 0.25,
                            "pitch_midi": 64,
                            "confidence": 1.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(["notes-to-tab", str(notes_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "e|0\nB|-\nG|-\nD|-\nA|-\nE|-\n")

    def test_notes_to_tab_without_left_hand_likelihood_stays_audio_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            notes_path = Path(tmpdir) / "notes.json"
            notes_path.write_text(
                json.dumps(
                    [
                        {
                            "start": 0.0,
                            "end": 0.25,
                            "pitch_midi": 68,
                            "confidence": 1.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(["notes-to-tab", str(notes_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "e|4\nB|-\nG|-\nD|-\nA|-\nE|-\n")

    def test_notes_to_tab_uses_left_hand_likelihood_for_fretted_candidate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            notes_path = tmp_path / "notes.json"
            likelihood_path = tmp_path / "likelihood.json"
            notes_path.write_text(
                json.dumps(
                    [
                        {
                            "start": 0.0,
                            "end": 0.25,
                            "pitch_midi": 68,
                            "confidence": 1.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            likelihood_path.write_text(
                json.dumps([{"time": 0.0, "likelihood": {"9": 1.0}}]),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "notes-to-tab",
                        str(notes_path),
                        "--left-hand-likelihood",
                        str(likelihood_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "e|-\nB|9\nG|-\nD|-\nA|-\nE|-\n")

    def test_notes_to_tab_left_hand_weight_can_favor_fretted_over_open(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            notes_path = tmp_path / "notes.json"
            likelihood_path = tmp_path / "likelihood.json"
            notes_path.write_text(
                json.dumps(
                    [
                        {
                            "start": 0.0,
                            "end": 0.25,
                            "pitch_midi": 64,
                            "confidence": 1.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            likelihood_path.write_text(
                json.dumps([{"time": 0.0, "likelihood": {"9": 1.0}}]),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "notes-to-tab",
                        str(notes_path),
                        "--left-hand-likelihood",
                        str(likelihood_path),
                        "--left-hand-weight",
                        "10",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.getvalue(), "e|-\nB|-\nG|9\nD|-\nA|-\nE|-\n")

    def test_notes_to_tab_invalid_json_is_readable_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            notes_path = Path(tmpdir) / "notes.json"
            notes_path.write_text("{not json", encoding="utf-8")
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(["notes-to-tab", str(notes_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("error: invalid JSON", errors.getvalue())
            self.assertIn("line 1, column 2", errors.getvalue())

    def test_notes_to_tab_sorts_loaded_note_events_before_rendering(self) -> None:
        captured_starts: list[float] = []

        def fake_render_notes_to_ascii_tab(notes, **kwargs):
            captured_starts.extend(note.start for note in notes)
            return "tab"

        original_render = cli.render_notes_to_ascii_tab
        cli.render_notes_to_ascii_tab = fake_render_notes_to_ascii_tab
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                notes_path = Path(tmpdir) / "notes.json"
                notes_path.write_text(
                    json.dumps(
                        [
                            {
                                "start": 0.5,
                                "end": 0.75,
                                "pitch_midi": 65,
                                "confidence": 1.0,
                            },
                            {
                                "start": 0.0,
                                "end": 0.25,
                                "pitch_midi": 64,
                                "confidence": 1.0,
                            },
                        ]
                    ),
                    encoding="utf-8",
                )

                exit_code = main(["notes-to-tab", str(notes_path)])
        finally:
            cli.render_notes_to_ascii_tab = original_render

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured_starts, [0.0, 0.5])

    def test_audio_only_notes_to_tab_smoke_test(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                ["notes-to-tab", str(FIXTURES_DIR / "audio_only_notes.json")]
            )

        tab_lines = output.getvalue().strip().splitlines()
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(tab_lines), 6)
        self.assertEqual(
            tab_lines,
            [
                "e|013",
                "B|---",
                "G|---",
                "D|---",
                "A|---",
                "E|---",
            ],
        )

    def test_audio_to_notes_writes_note_event_json(self) -> None:
        def fake_transcribe(audio_path: Path) -> list[NoteEvent]:
            self.assertEqual(audio_path, Path("input.wav"))
            return [
                NoteEvent(
                    start=0.0,
                    end=0.25,
                    pitch_midi=64,
                    confidence=0.9,
                    source="basic_pitch",
                )
            ]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "notes.json"
            original_transcribe = cli.transcribe_audio_to_notes
            cli.transcribe_audio_to_notes = fake_transcribe
            try:
                exit_code = main(["audio-to-notes", "input.wav", "--out", str(out_path)])
            finally:
                cli.transcribe_audio_to_notes = original_transcribe

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(out_path.read_text(encoding="utf-8")),
                [
                    {
                        "start": 0.0,
                        "end": 0.25,
                        "pitch_midi": 64,
                        "confidence": 0.9,
                        "source": "basic_pitch",
                    }
                ],
            )

    def test_audio_to_notes_writes_only_filtered_note_event_json(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=0.54,
                source="basic_pitch",
            ),
            NoteEvent(
                start=0.5,
                end=0.75,
                pitch_midi=65,
                confidence=0.55,
                source="basic_pitch",
            ),
            NoteEvent(
                start=1.0,
                end=1.25,
                pitch_midi=89,
                confidence=0.99,
                source="basic_pitch",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "notes.json"
            try:
                exit_code = main(
                    [
                        "audio-to-notes",
                        "input.wav",
                        "--out",
                        str(out_path),
                        "--min-confidence",
                        "0.55",
                        "--min-pitch",
                        "40",
                        "--max-pitch",
                        "88",
                    ]
                )
            finally:
                cli.transcribe_audio_to_notes = original_transcribe

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(out_path.read_text(encoding="utf-8")),
                [
                    {
                        "start": 0.5,
                        "end": 0.75,
                        "pitch_midi": 65,
                        "confidence": 0.55,
                        "source": "basic_pitch",
                    }
                ],
            )

    def test_audio_to_notes_writes_sorted_note_event_json(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.5,
                end=0.75,
                pitch_midi=65,
                confidence=0.9,
                source="basic_pitch",
            ),
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=0.9,
                source="basic_pitch",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "notes.json"
            try:
                exit_code = main(
                    ["audio-to-notes", "input.wav", "--out", str(out_path)]
                )
            finally:
                cli.transcribe_audio_to_notes = original_transcribe

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                [record["start"] for record in json.loads(out_path.read_text())],
                [0.0, 0.5],
            )

    def test_audio_to_notes_prints_stdout_without_output_file(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=0.9,
                source="basic_pitch",
            )
        ]
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exit_code = main(["audio-to-notes", "input.wav"])
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue()), [
            {
                "start": 0.0,
                "end": 0.25,
                "pitch_midi": 64,
                "confidence": 0.9,
                "source": "basic_pitch",
            }
        ])

    def test_audio_to_tab_writes_rendered_ascii_tab(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=1.0,
                source="basic_pitch",
            ),
            NoteEvent(
                start=0.5,
                end=0.75,
                pitch_midi=45,
                confidence=0.9,
                source="basic_pitch",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "tab.txt"
            try:
                exit_code = main(["audio-to-tab", "input.wav", "--out", str(out_path)])
            finally:
                cli.transcribe_audio_to_notes = original_transcribe

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                out_path.read_text(encoding="utf-8"),
                "e|0--\nB|---\nG|---\nD|---\nA|--0\nE|---",
            )

    def test_audio_to_tab_decodes_only_filtered_notes(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=32,
                confidence=0.99,
                source="basic_pitch",
            ),
            NoteEvent(
                start=0.25,
                end=0.5,
                pitch_midi=64,
                confidence=0.9,
                source="basic_pitch",
            ),
            NoteEvent(
                start=0.5,
                end=0.55,
                pitch_midi=65,
                confidence=0.9,
                source="basic_pitch",
            ),
        ]
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "audio-to-tab",
                        "input.wav",
                        "--min-pitch",
                        "40",
                        "--max-pitch",
                        "88",
                        "--min-duration",
                        "0.1",
                    ]
                )
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "e|-0\nB|--\nG|--\nD|--\nA|--\nE|--\n")

    def test_audio_to_tab_prints_stdout_without_output_file(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=64,
                confidence=1.0,
                source="basic_pitch",
            )
        ]
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exit_code = main(["audio-to-tab", "input.wav"])
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "e|0\nB|-\nG|-\nD|-\nA|-\nE|-\n")

    def test_audio_to_tab_uses_left_hand_likelihood_file(self) -> None:
        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = lambda audio_path: [
            NoteEvent(
                start=0.0,
                end=0.25,
                pitch_midi=68,
                confidence=1.0,
                source="basic_pitch",
            )
        ]
        output = io.StringIO()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                likelihood_path = Path(tmpdir) / "likelihood.json"
                likelihood_path.write_text(
                    json.dumps([{"time": 0.0, "likelihood": {"9": 1.0}}]),
                    encoding="utf-8",
                )
                with contextlib.redirect_stdout(output):
                    exit_code = main(
                        [
                            "audio-to-tab",
                            "input.wav",
                            "--left-hand-likelihood",
                            str(likelihood_path),
                        ]
                    )
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "e|-\nB|9\nG|-\nD|-\nA|-\nE|-\n")

    def test_landmarks_to_left_hand_likelihood_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            landmarks_path = tmp_path / "landmarks.json"
            out_path = tmp_path / "left_hand_likelihood.json"
            landmarks_path.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": 1.23,
                            "landmarks": [["left:index_finger_tip", 0.375, 0.52]],
                            "confidence": 0.9,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "landmarks-to-left-hand-likelihood",
                    str(landmarks_path),
                    "--max-fret",
                    "12",
                    "--out",
                    str(out_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            output = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(output[0]["time"], 1.23)
            self.assertEqual(
                max(output[0]["likelihood"], key=output[0]["likelihood"].get),
                "5",
            )

    def test_landmarks_to_left_hand_likelihood_invalid_max_fret_is_readable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            landmarks_path = Path(tmpdir) / "landmarks.json"
            landmarks_path.write_text(
                json.dumps([{"timestamp": 0.0, "landmarks": []}]),
                encoding="utf-8",
            )
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(
                    [
                        "landmarks-to-left-hand-likelihood",
                        str(landmarks_path),
                        "--max-fret",
                        "0",
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("error: max_fret must be positive", errors.getvalue())

    def test_frames_to_landmarks_writes_hand_landmark_json(self) -> None:
        calls: list[tuple[str, float, int]] = []

        def fake_frames_to_landmarks(
            frame_records,
            *,
            hand_index: int,
            mediapipe_model=None,
        ):
            self.assertIsNone(mediapipe_model)
            calls.extend(
                (str(record.path), record.timestamp, hand_index)
                for record in frame_records
            )
            return [
                HandLandmarkFrame(
                    timestamp=record.timestamp,
                    landmarks=(("left:index_finger_tip", 0.38, 0.52),),
                    confidence=0.9,
                )
                for record in frame_records
            ]

        original_frames_to_landmarks = cli.frame_images_to_hand_landmark_frames
        cli.frame_images_to_hand_landmark_frames = fake_frames_to_landmarks
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                frames_path = tmp_path / "frames.json"
                out_path = tmp_path / "hand_landmarks.json"
                frames_path.write_text(
                    json.dumps(
                        [
                            {"path": "frame_0001.png", "timestamp": 1.23},
                            {"path": "frame_0002.png", "timestamp": 1.27},
                        ]
                    ),
                    encoding="utf-8",
                )

                exit_code = main(
                    [
                        "frames-to-landmarks",
                        str(frames_path),
                        "--hand-index",
                        "1",
                        "--out",
                        str(out_path),
                    ]
                )

                self.assertEqual(exit_code, 0)
                self.assertEqual(
                    load_hand_landmark_frames_json(out_path),
                    [
                        HandLandmarkFrame(
                            timestamp=1.23,
                            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
                            confidence=0.9,
                        ),
                        HandLandmarkFrame(
                            timestamp=1.27,
                            landmarks=(("left:index_finger_tip", 0.38, 0.52),),
                            confidence=0.9,
                        ),
                    ],
                )
        finally:
            cli.frame_images_to_hand_landmark_frames = original_frames_to_landmarks

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            calls,
            [
                (str(tmp_path / "frame_0001.png"), 1.23, 1),
                (str(tmp_path / "frame_0002.png"), 1.27, 1),
            ],
        )

    def test_frames_to_landmarks_passes_mediapipe_model_path(self) -> None:
        calls: list[Path | None] = []

        def fake_frames_to_landmarks(
            frame_records,
            *,
            hand_index: int,
            mediapipe_model=None,
        ):
            self.assertEqual(hand_index, 0)
            calls.append(mediapipe_model)
            return [
                HandLandmarkFrame(
                    timestamp=record.timestamp,
                    landmarks=(("left:index_finger_tip", 0.38, 0.52),),
                    confidence=0.9,
                )
                for record in frame_records
            ]

        original_frames_to_landmarks = cli.frame_images_to_hand_landmark_frames
        cli.frame_images_to_hand_landmark_frames = fake_frames_to_landmarks
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                frames_path = tmp_path / "frames.json"
                out_path = tmp_path / "hand_landmarks.json"
                model_path = tmp_path / "hand_landmarker.task"
                frames_path.write_text(
                    json.dumps([{"path": "frame_0001.png", "timestamp": 1.23}]),
                    encoding="utf-8",
                )

                exit_code = main(
                    [
                        "frames-to-landmarks",
                        str(frames_path),
                        "--mediapipe-model",
                        str(model_path),
                        "--out",
                        str(out_path),
                    ]
                )
        finally:
            cli.frame_images_to_hand_landmark_frames = original_frames_to_landmarks

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [model_path])

    def test_frames_to_landmarks_invalid_hand_index_is_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            frames_path = Path(tmpdir) / "frames.json"
            frames_path.write_text(
                json.dumps([{"path": "frame_0001.png", "timestamp": 1.23}]),
                encoding="utf-8",
            )
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(
                    [
                        "frames-to-landmarks",
                        str(frames_path),
                        "--hand-index",
                        "-1",
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("error: hand_index must be non-negative", errors.getvalue())

    def test_frames_to_landmarks_invalid_json_is_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            frames_path = Path(tmpdir) / "frames.json"
            frames_path.write_text("{not json", encoding="utf-8")
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(["frames-to-landmarks", str(frames_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("error: invalid frame list JSON", errors.getvalue())

    def test_frames_to_landmarks_missing_mediapipe_is_readable(self) -> None:
        def fake_frames_to_landmarks(frame_records, *, hand_index: int, **kwargs):
            raise MediaPipeUnavailableError("MediaPipe is not installed")

        original_frames_to_landmarks = cli.frame_images_to_hand_landmark_frames
        cli.frame_images_to_hand_landmark_frames = fake_frames_to_landmarks
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                frames_path = Path(tmpdir) / "frames.json"
                frames_path.write_text(
                    json.dumps([{"path": "frame_0001.png", "timestamp": 1.23}]),
                    encoding="utf-8",
                )
                errors = io.StringIO()

                with contextlib.redirect_stderr(errors):
                    exit_code = main(["frames-to-landmarks", str(frames_path)])
        finally:
            cli.frame_images_to_hand_landmark_frames = original_frames_to_landmarks

        self.assertEqual(exit_code, 1)
        self.assertIn("error: MediaPipe is not installed", errors.getvalue())

    def test_calibrate_landmarks_help(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as exc:
                main(["calibrate-landmarks", "--help"])

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("usage: tabgen calibrate-landmarks", output.getvalue())

    def test_calibrate_landmarks_writes_hand_landmark_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            landmarks_path = tmp_path / "image_landmarks.json"
            calibration_path = tmp_path / "calibration.json"
            out_path = tmp_path / "fretboard_landmarks.json"
            landmarks_path.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": 1.23,
                            "landmarks": [
                                ["left:index_finger_tip", 190.0, 45.0],
                                ["wrist", 10.0, 20.0],
                            ],
                            "confidence": 0.9,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            calibration_path.write_text(
                json.dumps(
                    {
                        "nut_string_6": [10.0, 20.0],
                        "nut_string_1": [10.0, 120.0],
                        "bridge_string_6": [250.0, 20.0],
                        "bridge_string_1": [250.0, 120.0],
                        "timestamp": 0.0,
                    }
                ),
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "calibrate-landmarks",
                    str(landmarks_path),
                    "--calibration",
                    str(calibration_path),
                    "--out",
                    str(out_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                load_hand_landmark_frames_json(out_path),
                [
                    HandLandmarkFrame(
                        timestamp=1.23,
                        landmarks=(
                            ("left:index_finger_tip", 0.75, 0.25),
                            ("wrist", 0.0, 0.0),
                        ),
                        confidence=0.9,
                    )
                ],
            )

    def test_calibrate_landmarks_invalid_calibration_is_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            landmarks_path = tmp_path / "image_landmarks.json"
            calibration_path = tmp_path / "calibration.json"
            landmarks_path.write_text(
                json.dumps([{"timestamp": 0.0, "landmarks": []}]),
                encoding="utf-8",
            )
            calibration_path.write_text("{not json", encoding="utf-8")
            errors = io.StringIO()

            with contextlib.redirect_stderr(errors):
                exit_code = main(
                    [
                        "calibrate-landmarks",
                        str(landmarks_path),
                        "--calibration",
                        str(calibration_path),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "error: invalid fretboard calibration JSON",
                errors.getvalue(),
            )

    def test_audio_command_missing_basic_pitch_is_readable_error(self) -> None:
        def fake_transcribe(audio_path: Path) -> list[NoteEvent]:
            raise BasicPitchUnavailableError("Basic Pitch is not installed")

        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = fake_transcribe
        errors = io.StringIO()
        try:
            with contextlib.redirect_stderr(errors):
                exit_code = main(["audio-to-notes", "input.wav"])
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 1)
        self.assertIn("error: Basic Pitch is not installed", errors.getvalue())

    def test_audio_command_invalid_threshold_combination_is_readable_error(self) -> None:
        def fail_if_called(audio_path: Path) -> list[NoteEvent]:
            raise AssertionError("transcription should not run for invalid thresholds")

        original_transcribe = cli.transcribe_audio_to_notes
        cli.transcribe_audio_to_notes = fail_if_called
        errors = io.StringIO()
        try:
            with contextlib.redirect_stderr(errors):
                exit_code = main(
                    [
                        "audio-to-notes",
                        "input.wav",
                        "--min-pitch",
                        "89",
                        "--max-pitch",
                        "88",
                    ]
                )
        finally:
            cli.transcribe_audio_to_notes = original_transcribe

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "error: min_pitch must be less than or equal to max_pitch",
            errors.getvalue(),
        )

    def test_audio_command_invalid_min_confidence_is_readable_error(self) -> None:
        errors = io.StringIO()

        with contextlib.redirect_stderr(errors):
            exit_code = main(
                ["audio-to-tab", "input.wav", "--min-confidence", "1.1"]
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("error: min_confidence", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
