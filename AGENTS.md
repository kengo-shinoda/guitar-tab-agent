# AGENTS.md

This project builds a video-assisted guitar tablature transcription app.

## Product goal

Generate editable guitar tablature from guitar performance videos by combining:
- audio transcription,
- hand/fretboard video evidence,
- guitar-specific playability constraints,
- human-in-the-loop correction.

The MVP target is not perfect publication-quality notation. The MVP target is a useful, editable TAB candidate that reduces manual transcription effort.

## Core principles

- Avoid reinventing wheels.
- Prefer existing open-source models and libraries.
- Do not train custom models unless an issue explicitly requests it.
- Keep audio, video, fusion, and output layers decoupled.
- Use deterministic, testable components where possible.
- Favor transparent scoring and confidence outputs over black-box behavior.
- Every implementation PR must include tests or a clear explanation why tests are not possible.

## MVP constraints

- Standard tuning only.
- Six-string guitar only.
- Phase 0 and Phase 1 are intentionally limited to six-string standard-tuning guitar.
- Manual fretboard calibration first.
- Fixed-camera videos first.
- Solo guitar or guitar-forward recordings first.
- ASCII TAB and JSON outputs first.
- MusicXML, GuitarPro, and web UI are later phases.
- 7-string guitar, bass guitar, and custom tunings are future work; do not implement them unless an issue explicitly requests it.
- No automatic model training in MVP.

## Architecture

- Python package name: `guitar_tab_agent`.
- CLI command name: `tabgen`.
- `tabgen` is the command-line executable, not the Python package name.
- `src/guitar_tab_agent/audio/`: audio extraction and audio-to-note adapters.
- `src/guitar_tab_agent/video/`: frame extraction, calibration, hand tracking.
- `src/guitar_tab_agent/fusion/`: string/fret candidate generation, cost model, decoding.
- `src/guitar_tab_agent/tab/`: TAB rendering and export.
- `src/guitar_tab_agent/cli.py`: command-line interface backing the `tabgen` command.
- `docs/`: product requirements, architecture, evaluation, roadmap.
- `tests/`: unit and integration tests.

## Coding rules

- Do not make broad refactors.
- Do not introduce new dependencies without explaining why.
- Do not change public interfaces unless the issue asks for it.
- Prefer small PRs.
- Keep functions small and typed.
- Use dataclasses or pydantic-style schemas for internal data structures, but do not add pydantic unless justified.
- Do not add broad instrument/tuning abstractions before they are requested. When writing new code, avoid unnecessary hard-coding of six strings if a small, local abstraction would keep the code easy to extend later.
- Each PR must include:
  - Summary
  - Tests run
  - Known limitations

## Testing rules

- Primary test command: `uv run pytest`.
- Prefer unit tests with mocks or synthetic fixtures.
- Avoid requiring large audio/video files in unit tests.
- Avoid network access in tests.
- Any optional dependency integration must have graceful failure or skip behavior.
- Add regression tests for decoding and pitch-to-fret mapping.

## Review guidelines

Treat the following as high-priority issues:
- Wrong pitch-to-string/fret mapping.
- Hidden assumptions about tuning.
- Premature support claims for 7-string guitar, bass guitar, or custom tunings.
- Unclear coordinate systems.
- Unstable public interfaces.
- Unnecessary dependency additions.
- Changes that make later multimodal fusion difficult.
- Unreviewed generated code that touches many unrelated files.

## When uncertain

Ask for a design note instead of implementing a speculative large feature.
Prefer documenting assumptions in `docs/architecture.md` before coding.
