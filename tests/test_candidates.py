import unittest

from guitar_tab_agent.fusion.candidates import DEFAULT_MAX_FRET, candidate_positions_for_midi
from guitar_tab_agent.schema import STANDARD_TUNING_MIDI, StringFretCandidate


class CandidatePositionsTest(unittest.TestCase):
    def test_default_max_fret_is_24(self) -> None:
        self.assertEqual(DEFAULT_MAX_FRET, 24)

    def test_open_strings_match_standard_tuning(self) -> None:
        for string, pitch_midi in STANDARD_TUNING_MIDI.items():
            with self.subTest(string=string, pitch_midi=pitch_midi):
                positions = candidate_positions_for_midi(pitch_midi, max_fret=0)

                self.assertEqual(
                    positions,
                    (
                        StringFretCandidate(
                            string=string,
                            fret=0,
                            pitch_midi=pitch_midi,
                        ),
                    ),
                )

    def test_low_e_has_one_open_position(self) -> None:
        positions = candidate_positions_for_midi(40)

        self.assertEqual(
            [(p.string, p.fret, p.pitch_midi) for p in positions],
            [(6, 0, 40)],
        )

    def test_high_e_open_with_zero_max_fret(self) -> None:
        positions = candidate_positions_for_midi(64, max_fret=0)

        self.assertEqual(
            [(p.string, p.fret, p.pitch_midi) for p in positions],
            [(1, 0, 64)],
        )

    def test_pitch_can_have_multiple_positions(self) -> None:
        positions = candidate_positions_for_midi(64, max_fret=24)

        self.assertEqual(
            [(p.string, p.fret, p.pitch_midi) for p in positions],
            [
                (1, 0, 64),
                (2, 5, 64),
                (3, 9, 64),
                (4, 14, 64),
                (5, 19, 64),
                (6, 24, 64),
            ],
        )

    def test_valid_midi_below_guitar_range_returns_no_positions(self) -> None:
        self.assertEqual(candidate_positions_for_midi(39), ())

    def test_valid_midi_above_default_max_fret_range_returns_no_positions(self) -> None:
        self.assertEqual(candidate_positions_for_midi(89), ())

    def test_max_fret_limits_candidates(self) -> None:
        positions = candidate_positions_for_midi(64, max_fret=4)

        self.assertEqual([(p.string, p.fret) for p in positions], [(1, 0)])

    def test_invalid_pitch_raises(self) -> None:
        with self.assertRaises(ValueError):
            candidate_positions_for_midi(128)

    def test_negative_pitch_raises(self) -> None:
        with self.assertRaises(ValueError):
            candidate_positions_for_midi(-1)

    def test_negative_max_fret_raises(self) -> None:
        with self.assertRaises(ValueError):
            candidate_positions_for_midi(64, max_fret=-1)


if __name__ == "__main__":
    unittest.main()
