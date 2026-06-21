import contextlib
import io
import json
import unittest

from guitar_tab_agent.cli import main


class CliTest(unittest.TestCase):
    def test_candidates_json(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["candidates", "64", "--max-fret", "0", "--json"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(output.getvalue()),
            [{"string_number": 1, "fret_number": 0}],
        )

    def test_no_command_prints_help(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("usage: tabgen", output.getvalue())


if __name__ == "__main__":
    unittest.main()
