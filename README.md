# guitar-tab-agent

`guitar-tab-agent` generates editable guitar TAB drafts from guitar performance
inputs. The current short-term focus is an audio-only CLI MVP for clean,
monophonic guitar phrases.

The Python package is `guitar_tab_agent`. The CLI command is `tabgen`.

## Current Status

The project is in audio-only CLI MVP development. The known-good path is:

```text
audio input -> Basic Pitch NoteEvents -> chronological sorting
            -> ergonomic decoder -> ASCII TAB
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

## Important Limitations

- Audio alone cannot uniquely determine exact guitar string/fret positions.
- The current decoder chooses a playable ergonomic fingering path, not observed
  ground-truth fingering.
- The current target is clean monophonic or mostly single-note guitar phrases.
- Chords, bends, heavy distortion, full-mix source separation, and exact
  technique notation are not solved yet.
- Video-assisted evidence exists as advanced/future work, but it is not the
  public MVP path.

## Deeper Docs

- [Audio-only MVP scope](docs/audio_only_mvp.md)
- [Audio-only smoke checkpoint](docs/audio_only_smoke_checkpoint.md)
- [Architecture](docs/architecture.md)
- Future/advanced video material:
  - [Real-image hand landmark smoke test](docs/real_image_hand_landmark_smoke.md)
  - [Video-assisted smoke test](docs/video_assisted_smoke_test.md)
  - [Future multimodal fusion](docs/future_multimodal_fusion.md)

## Local Development

Run tests:

```bash
uv run pytest
```
