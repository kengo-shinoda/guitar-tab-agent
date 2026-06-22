"""Command-line interface for guitar-tab-agent."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from guitar_tab_agent import __version__
from guitar_tab_agent.audio.basic_pitch_adapter import (
    BasicPitchUnavailableError,
    transcribe_audio_to_notes,
)
from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi
from guitar_tab_agent.fusion.simple_decoder import decode_audio_notes
from guitar_tab_agent.schema import NoteEvent
from guitar_tab_agent.tab.ascii_tab import render_ascii_tab


def _load_note_events(path: Path) -> list[NoteEvent]:
    try:
        raw_notes = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc

    if not isinstance(raw_notes, list):
        raise ValueError(f"expected a JSON list of NoteEvent records in {path}")

    notes: list[NoteEvent] = []
    for index, raw_note in enumerate(raw_notes):
        if not isinstance(raw_note, dict):
            raise ValueError(f"note record at index {index} must be a JSON object")
        try:
            notes.append(NoteEvent(**raw_note))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid NoteEvent record at index {index}: {exc}"
            ) from exc

    return notes


def _notes_to_json(notes: Sequence[NoteEvent]) -> str:
    return json.dumps([asdict(note) for note in notes], indent=2)


def _write_or_print(content: str, output_path: Path | None) -> None:
    if output_path is None:
        print(content)
    else:
        output_path.write_text(content, encoding="utf-8")


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

    notes_to_tab = subparsers.add_parser(
        "notes-to-tab",
        help="convert JSON NoteEvent records to ASCII TAB",
    )
    notes_to_tab.add_argument("notes_json", type=Path)
    notes_to_tab.add_argument(
        "--out",
        type=Path,
        help="write ASCII TAB to this file instead of stdout",
    )

    audio_to_notes = subparsers.add_parser(
        "audio-to-notes",
        help="transcribe an audio file to JSON NoteEvent records",
    )
    audio_to_notes.add_argument("audio_path", type=Path)
    audio_to_notes.add_argument(
        "--out",
        type=Path,
        help="write NoteEvent JSON to this file instead of stdout",
    )

    audio_to_tab = subparsers.add_parser(
        "audio-to-tab",
        help="transcribe an audio file and render audio-only ASCII TAB",
    )
    audio_to_tab.add_argument("audio_path", type=Path)
    audio_to_tab.add_argument(
        "--out",
        type=Path,
        help="write ASCII TAB to this file instead of stdout",
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
                print(f"string={position.string} fret={position.fret}")
        return 0

    if args.command == "notes-to-tab":
        try:
            notes = _load_note_events(args.notes_json)
            tab = render_ascii_tab(decode_audio_notes(notes))
            _write_or_print(tab, args.out)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: could not write {args.out}: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "audio-to-notes":
        try:
            notes = transcribe_audio_to_notes(args.audio_path)
            _write_or_print(_notes_to_json(notes), args.out)
        except BasicPitchUnavailableError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: could not write {args.out}: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "audio-to-tab":
        try:
            notes = transcribe_audio_to_notes(args.audio_path)
            tab = render_ascii_tab(decode_audio_notes(notes))
            _write_or_print(tab, args.out)
        except BasicPitchUnavailableError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: could not write {args.out}: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
