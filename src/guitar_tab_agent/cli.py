"""Command-line interface for guitar-tab-agent."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from guitar_tab_agent import __version__
from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tabgen",
        description="Generate editable guitar TAB candidates from performance videos.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    candidates = subparsers.add_parser(
        "candidates",
        help="list standard-tuning string/fret candidates for a MIDI pitch",
    )
    candidates.add_argument("midi_pitch", type=int)
    candidates.add_argument("--max-fret", type=int, default=24)
    candidates.add_argument(
        "--json",
        action="store_true",
        help="print candidates as JSON",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "candidates":
        positions = candidate_positions_for_midi(
            args.midi_pitch,
            max_fret=args.max_fret,
        )
        if args.json:
            print(json.dumps([asdict(position) for position in positions], indent=2))
        else:
            for position in positions:
                print(f"string={position.string_number} fret={position.fret_number}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
