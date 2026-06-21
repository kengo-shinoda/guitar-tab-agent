import unittest

from guitar_tab_agent.schema import DecodedTabEvent
from guitar_tab_agent.tab.ascii import render_ascii_tab


class RenderAsciiTabTest(unittest.TestCase):
    def test_renders_six_strings_in_tab_order(self) -> None:
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
            ]
        )

        self.assertEqual(
            tab.splitlines(),
            [
                "e|0----",
                "B|-----",
                "G|-----",
                "D|-----",
                "A|---0-",
                "E|-----",
            ],
        )

    def test_empty_input_renders_empty_tab_lines(self) -> None:
        tab = render_ascii_tab([])

        self.assertEqual(tab, "e|\nB|\nG|\nD|\nA|\nE|")


if __name__ == "__main__":
    unittest.main()
