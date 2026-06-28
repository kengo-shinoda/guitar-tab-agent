# guitar-tab-agent

`guitar-tab-agent` is a local-first tool for turning short, clean guitar audio
into playable, editable guitar TAB drafts.

Unlike generic audio transcription, guitar TAB generation has a structural
ambiguity: the same pitch can usually be played on multiple string/fret
positions. This project exposes that ambiguity by generating multiple TAB
candidates for human review, rather than claiming to recover exact ground-truth
fingering from audio alone.

The current short-term focus is an audio-only CLI and local web MVP for clean,
monophonic or mostly single-note guitar phrases.

The Python package is `guitar_tab_agent`. The CLI command is `tabgen`.

## Current Status

The project is in audio-only CLI/local web MVP development. The known-good path
is:

```text
audio input -> Basic Pitch NoteEvents -> chronological sorting
            -> ergonomic decoder -> ASCII TAB candidates
```

The output should be treated as a playable, editable TAB draft. It is not a
guarantee of the exact string/fret positions used by the player.

## What Works Now

- `tabgen audio-to-notes`: transcribe audio into `NoteEvent` JSON through the
  optional Basic Pitch adapter.
- `tabgen audio-to-tab`: transcribe audio and render an ASCII TAB draft.
- `tabgen notes-to-tab`: render ASCII TAB from existing `NoteEvent` JSON.
- `tabgen candidates`: list standard-tuning string/fret candidates for a MIDI
  pitch.
- `tabgen web`: run a minimal local browser UI for the audio-to-TAB path.

## Quick Start

Install project and development dependencies:

```bash
uv sync
```

For real audio transcription commands, install the optional Basic Pitch package
into the same environment:

```bash
uv pip install basic-pitch
```

You can skip Basic Pitch when using commands that do not transcribe audio, such
as `notes-to-tab` and `candidates`.

Inspect the CLI:

```bash
uv run tabgen --help
```

Generate a TAB draft from clean guitar audio:

```bash
uv run tabgen audio-to-tab input.wav \
  --out tab.txt \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88
```

Run the minimal local web UI:

```bash
uv run tabgen web
```

Then open the printed local URL, upload a clean guitar audio file, optionally
set the same basic filters, and generate an ASCII TAB draft. The web UI uses
Python's standard library for local serving, so there is no separate web
dependency. Real audio transcription still requires Basic Pitch:

```bash
uv pip install basic-pitch
```

## CLI Examples

Write `NoteEvent` JSON from audio:

```bash
uv run tabgen audio-to-notes input.wav \
  --out notes.json \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88
```

Write TAB directly from audio:

```bash
uv run tabgen audio-to-tab input.wav \
  --out tab.txt \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88
```

Render TAB from existing notes JSON:

```bash
uv run tabgen notes-to-tab notes.json --out tab.txt
```

List candidate positions for a MIDI pitch:

```bash
uv run tabgen candidates 64
```

Run the local web UI:

```bash
uv run tabgen web --host 127.0.0.1 --port 8765
```

To open the browser automatically:

```bash
uv run tabgen web --open-browser
```

## Important Limitations

- Audio alone cannot uniquely determine exact guitar string/fret positions.
- The current decoder chooses playable ergonomic fingering candidates, not
  observed ground-truth fingering.
- The current target is clean monophonic or mostly single-note guitar phrases.
- Chords, bends, heavy distortion, full-mix source separation, and exact
  technique notation are not solved yet.
- Video-assisted evidence exists as advanced/future work, but it is not the
  public MVP path.
- The local web UI is intentionally minimal: no authentication, no persistence,
  no editing UI, no waveform display, no source separation, and no video/hand
  tracking controls.

## License and commercial use

The open-source core is released under the Apache License 2.0. The public
repository is intended to provide the local-first engine, CLI, development web
UI, and documentation.

Hosted services, mobile applications, account systems, billing, and polished
commercial user experiences can be developed as separate layers on top of this
core. Any commercial deployment should also review the licenses of optional
third-party dependencies and avoid using unlicensed third-party audio or video
material in demos, tests, or user-facing examples.

## Deeper Docs

- [Audio-only MVP scope](docs/audio_only_mvp.md)
- [Audio-only smoke checkpoint](docs/audio_only_smoke_checkpoint.md)
- [Local web UI smoke checkpoint](docs/local_web_smoke_checkpoint.md)
- [Architecture](docs/architecture.md)
- [Current state handoff](docs/current_state.md)
- [Codex for OSS maintenance plan](docs/codex_for_oss_plan.md)
- [Public alpha release checklist](docs/public_alpha_release_checklist.md)
- Future/advanced video material:
  - [Real-image hand landmark smoke test](docs/real_image_hand_landmark_smoke.md)
  - [Video-assisted smoke test](docs/video_assisted_smoke_test.md)
  - [Future multimodal fusion](docs/future_multimodal_fusion.md)

## Local Development

Run tests:

```bash
uv run pytest
```
