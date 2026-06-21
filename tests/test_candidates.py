import unittest

from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi


class CandidatePositionsTest(unittest.TestCase):
    def test_low_e_has_one_open_position(self) -> None:
        positions = candidate_positions_for_midi(40)

        self.assertEqual([(p.string, p.fret, p.pitch_midi) for p in positions], [(6, 0, 40)])

    def test_high_e_open_with_zero_max_fret(self) -> None:
        positions = candidate_positions_for_midi(64, max_fret=0)

        self.assertEqual([(p.string, p.fret, p.pitch_midi) for p in positions], [(1, 0, 64)])

    def test_pitch_can_have_multiple_positions(self) -> None:
        positions = candidate_positions_for_midi(64, max_fret=24)

        self.assertIn((1, 0), [(p.string, p.fret) for p in positions])
        self.assertIn((2, 5), [(p.string, p.fret) for p in positions])
        self.assertIn((3, 9), [(p.string, p.fret) for p in positions])

    def test_invalid_pitch_raises(self) -> None:
        with self.assertRaises(ValueError):
            candidate_positions_for_midi(128)


if __name__ == "__main__":
    unittest.main()
