import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import guitar_tab_agent.cli as cli
from guitar_tab_agent.audio.basic_pitch_adapter import BasicPitchUnavailableError
from guitar_tab_agent.cli import main
from guitar_tab_agent.schema import NoteEvent


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
