import unittest

from guitar_tab_agent.schema import DecodedTabEvent
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab


class RenderAsciiTabTest(unittest.TestCase):
    def test_empty_input_renders_empty_tab_lines(self) -> None:
        tab = render_ascii_tab([])

        self.assertEqual(tab, "e|\nB|\nG|\nD|\nA|\nE|")

    def test_single_note(self) -> None:
        tab = render_ascii_tab(
            [
                DecodedTabEvent(
                    start=0.0,
                    end=0.25,
                    string=1,
                    fret=3,
                    pitch_midi=67,
                    confidence=1.0,
                ),
            ]
        )

        self.assertEqual(
            tab,
            "e|3\nB|-\nG|-\nD|-\nA|-\nE|-",
        )

    def test_sequence_uses_quantized_time_positions(self) -> None:
        tab = render_ascii_tab(
            [
                DecodedTabEvent(
                    start=0.0,
                    end=0.25,
                    string=1,
                    fret=0,
                    pitch_midi=64,
                    confidence=1.0,
                ),
                DecodedTabEvent(
                    start=0.5,
                    end=0.75,
                    string=5,
                    fret=0,
                    pitch_midi=45,
                    confidence=1.0,
                ),
            ],
            seconds_per_column=0.25,
        )

        self.assertEqual(
            tab,
            "e|0--\nB|---\nG|---\nD|---\nA|--0\nE|---",
        )

    def test_two_digit_frets_widen_time_slot(self) -> None:
        tab = render_ascii_tab(
            [
                DecodedTabEvent(
                    start=0.0,
                    end=0.25,
                    string=2,
                    fret=10,
                    pitch_midi=69,
                    confidence=0.8,
                ),
                DecodedTabEvent(
                    start=0.25,
                    end=0.5,
                    string=1,
                    fret=3,
                    pitch_midi=67,
                    confidence=0.8,
                ),
            ],
            seconds_per_column=0.25,
        )

        self.assertEqual(
            tab,
            "e|--3\nB|10-\nG|---\nD|---\nA|---\nE|---",
        )

    def test_output_is_deterministic(self) -> None:
        events = [
            DecodedTabEvent(
                start=0.5,
                end=0.75,
                string=3,
                fret=7,
                pitch_midi=62,
                confidence=0.9,
            ),
            DecodedTabEvent(
                start=0.0,
                end=0.25,
                string=1,
                fret=5,
                pitch_midi=69,
                confidence=0.9,
            ),
        ]

        self.assertEqual(render_ascii_tab(events), render_ascii_tab(list(reversed(events))))

    def test_rejects_non_positive_quantization(self) -> None:
        with self.assertRaisesRegex(ValueError, "seconds_per_column"):
            render_ascii_tab([], seconds_per_column=0)


if __name__ == "__main__":
    unittest.main()
