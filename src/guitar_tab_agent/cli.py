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
from guitar_tab_agent.audio.note_filtering import (
    filter_note_events,
    validate_note_filter_thresholds,
)
from guitar_tab_agent.fusion.candidates import candidate_positions_for_midi
from guitar_tab_agent.fusion.simple_decoder import (
    DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
    LeftHandFretLikelihoodByTime,
)
from guitar_tab_agent.schema import NoteEvent
from guitar_tab_agent.video.frame_list_json import load_frame_image_records_json
from guitar_tab_agent.video.left_hand_likelihood_json import (
    load_left_hand_fret_likelihood_json,
)
from guitar_tab_agent.video.hand_landmark_frame_json import (
    load_hand_landmark_frames_json,
)
from guitar_tab_agent.video.hand_tracking import MediaPipeUnavailableError
from guitar_tab_agent.workflows import (
    frame_images_to_hand_landmark_frames,
    hand_landmark_frames_to_json,
    hand_landmark_frames_to_left_hand_likelihood_json,
    render_notes_to_ascii_tab,
)


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


def _add_audio_filter_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        help="drop notes with confidence below this value",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=None,
        help="drop notes shorter than this duration in seconds",
    )
    parser.add_argument(
        "--min-pitch",
        type=int,
        default=None,
        help="drop notes below this MIDI pitch",
    )
    parser.add_argument(
        "--max-pitch",
        type=int,
        default=None,
        help="drop notes above this MIDI pitch",
    )


def _add_left_hand_likelihood_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--left-hand-likelihood",
        type=Path,
        default=None,
        help=(
            "optional JSON evidence keyed by note start time; each record maps "
            "frets 1..max_fret to likelihood scores"
        ),
    )
    parser.add_argument(
        "--left-hand-weight",
        type=float,
        default=DEFAULT_LEFT_HAND_EVIDENCE_WEIGHT,
        help=(
            "decoder evidence weight for --left-hand-likelihood; open strings "
            "receive neutral left-hand evidence"
        ),
    )


def _filter_transcribed_notes(args: argparse.Namespace) -> list[NoteEvent]:
    validate_note_filter_thresholds(
        min_confidence=args.min_confidence,
        min_duration=args.min_duration,
        min_pitch=args.min_pitch,
        max_pitch=args.max_pitch,
    )
    notes = transcribe_audio_to_notes(args.audio_path)
    return filter_note_events(
        notes,
        min_confidence=args.min_confidence,
        min_duration=args.min_duration,
        min_pitch=args.min_pitch,
        max_pitch=args.max_pitch,
    )


def _load_left_hand_likelihood_arg(
    args: argparse.Namespace,
) -> LeftHandFretLikelihoodByTime | None:
    if args.left_hand_likelihood is None:
        return None
    return load_left_hand_fret_likelihood_json(args.left_hand_likelihood)


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
    _add_left_hand_likelihood_arguments(notes_to_tab)

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
    _add_audio_filter_arguments(audio_to_notes)

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
    _add_audio_filter_arguments(audio_to_tab)
    _add_left_hand_likelihood_arguments(audio_to_tab)

    landmarks_to_likelihood = subparsers.add_parser(
        "landmarks-to-left-hand-likelihood",
        help="convert HandLandmarkFrame JSON to left-hand likelihood JSON",
    )
    landmarks_to_likelihood.add_argument("landmarks_json", type=Path)
    landmarks_to_likelihood.add_argument(
        "--max-fret",
        type=int,
        default=24,
        help="maximum fret region to score",
    )
    landmarks_to_likelihood.add_argument(
        "--out",
        type=Path,
        help="write left-hand likelihood JSON to this file instead of stdout",
    )

    frames_to_landmarks = subparsers.add_parser(
        "frames-to-landmarks",
        help="extract HandLandmarkFrame JSON from frame images",
    )
    frames_to_landmarks.add_argument("frames_json", type=Path)
    frames_to_landmarks.add_argument(
        "--hand-index",
        type=int,
        default=0,
        help="detected hand index to export",
    )
    frames_to_landmarks.add_argument(
        "--out",
        type=Path,
        help="write HandLandmarkFrame JSON to this file instead of stdout",
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
            tab = render_notes_to_ascii_tab(
                notes,
                left_hand_fret_likelihood_by_time=_load_left_hand_likelihood_arg(args),
                left_hand_weight=args.left_hand_weight,
            )
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
            notes = _filter_transcribed_notes(args)
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
            notes = _filter_transcribed_notes(args)
            tab = render_notes_to_ascii_tab(
                notes,
                left_hand_fret_likelihood_by_time=_load_left_hand_likelihood_arg(args),
                left_hand_weight=args.left_hand_weight,
            )
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

    if args.command == "landmarks-to-left-hand-likelihood":
        try:
            frames = load_hand_landmark_frames_json(args.landmarks_json)
            likelihood_json = hand_landmark_frames_to_left_hand_likelihood_json(
                frames,
                max_fret=args.max_fret,
            )
            _write_or_print(likelihood_json, args.out)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: could not write {args.out}: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "frames-to-landmarks":
        try:
            frame_records = load_frame_image_records_json(args.frames_json)
            landmark_frames = frame_images_to_hand_landmark_frames(
                frame_records,
                hand_index=args.hand_index,
            )
            _write_or_print(hand_landmark_frames_to_json(landmark_frames), args.out)
        except MediaPipeUnavailableError as exc:
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
