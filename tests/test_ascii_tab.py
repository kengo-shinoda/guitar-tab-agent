import unittest

from guitar_tab_agent.models import NoteEvent, TabEvent, TabPosition
from guitar_tab_agent.tab.ascii import render_ascii_tab


class RenderAsciiTabTest(unittest.TestCase):
    def test_renders_six_strings_in_tab_order(self) -> None:
        tab = render_ascii_tab(
            [
                TabEvent(
                    note=NoteEvent(onset=0.0, duration=0.25, midi_pitch=64),
                    position=TabPosition(string_number=1, fret_number=0),
                ),
                TabEvent(
                    note=NoteEvent(onset=0.5, duration=0.25, midi_pitch=45),
                    position=TabPosition(string_number=5, fret_number=0),
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

    def test_unpositioned_events_are_omitted(self) -> None:
        tab = render_ascii_tab(
            [TabEvent(note=NoteEvent(onset=0.0, duration=0.25, midi_pitch=64))]
        )

        self.assertEqual(tab, "e|\nB|\nG|\nD|\nA|\nE|")


if __name__ == "__main__":
    unittest.main()
