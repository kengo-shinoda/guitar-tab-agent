# AGENTS.md

This project currently builds a local-first, audio-only guitar tablature draft generator. The public MVP turns short, clean guitar audio into editable, human-reviewable TAB candidates.

Video-assisted evidence is future work. Future versions may use fretboard calibration and left-hand evidence to reduce string/fret ambiguity, but the current public-alpha path should be framed as audio-only unless a specific issue asks for video work.

## Product goal

Generate editable guitar tablature drafts by combining:
- audio-derived note events,
- guitar-specific playability constraints,
- ranked string/fret candidate generation,
- ergonomic scoring,
- human-in-the-loop review and correction.

Future multimodal work may add:
- hand/fretboard video evidence,
- manual fretboard calibration,
- left-hand likelihood signals,
- right-hand string evidence.

The MVP target is not perfect publication-quality notation. The MVP target is a useful, editable TAB candidate that reduces manual transcription effort while making ambiguity visible.

## Core principles

- Avoid reinventing wheels.
- Prefer existing open-source models and libraries.
- Do not train custom models unless an issue explicitly requests it.
- Keep audio, future video, fusion, and output layers decoupled.
- Use deterministic, testable components where possible.
- Favor transparent scoring and confidence outputs over black-box behavior.
- Every implementation PR must include tests or a clear explanation why tests are not possible.

## MVP constraints

- Audio-only public MVP.
- Standard tuning only.
- Six-string guitar only.
- Short, clean, guitar-forward audio first.
- Monophonic or mostly single-note phrases first.
- ASCII TAB and JSON outputs first.
- Local CLI and minimal local web UI first.
- Candidate review and correction workflows before broader notation export.
- Video/left-hand evidence is future work, not the public-alpha claim.
- 7-string guitar, bass guitar, and custom tunings are future work; do not implement them unless an issue explicitly requests it.
- No automatic model training in MVP.

## Architecture

- Python package name: `guitar_tab_agent`.
- CLI command name: `tabgen`.
- `tabgen` is the command-line executable, not the Python package name.
- `src/guitar_tab_agent/audio/`: audio-to-note adapters and note filtering.
- `src/guitar_tab_agent/video/`: future frame extraction, calibration, and hand tracking.
- `src/guitar_tab_agent/fusion/`: string/fret candidate generation, cost model, decoding.
- `src/guitar_tab_agent/tab/`: TAB rendering and export.
- `src/guitar_tab_agent/web/`: minimal local web UI for audio-to-TAB workflows.
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
- Premature support claims for 7-string guitar, bass guitar, custom tunings, dense polyphony, or exact observed fingering recovery.
- Confusing the audio-only public MVP with future video-assisted work.
- Unclear coordinate systems in future video modules.
- Unstable public interfaces.
- Unnecessary dependency additions.
- Changes that make later multimodal fusion difficult.
- Unreviewed generated code that touches many unrelated files.

## When uncertain

Ask for a design note instead of implementing a speculative large feature.
Prefer documenting assumptions in `docs/architecture.md` before coding.
