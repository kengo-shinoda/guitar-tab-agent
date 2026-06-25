# Local Golden Audio Test Protocol

This document defines how to build a small local golden audio set for the current audio-only TAB generation MVP.

The goal is not to create a public dataset. The goal is to keep a controlled, repeatable set of self-recorded clips that can be used to evaluate the known-good path:

```text
audio -> NoteEvents -> ergonomic string/fret decoder -> ASCII TAB
```

Audio files and generated artifacts must stay outside the repository.

## Why local self-recorded clips first

External datasets are useful later, but they are not the best first smoke source.

At the current stage, we need clips where the intended phrase, intended fingering, tuning, recording setup, and mistakes are known. That makes failures interpretable:

- pitch extraction failure
- note filtering failure
- chronological ordering failure
- string/fret ambiguity
- decoder path choice
- recording-quality problem
- expected-fingering mismatch

A small self-recorded golden set should come before broad external benchmark use.

## Repository policy

Do not commit:

- `.wav`, `.mp3`, `.m4a`, `.flac`, or other audio files
- generated NoteEvent JSON
- generated TAB text
- screenshots
- logs
- downloaded datasets
- copyrighted media
- local model artifacts

It is acceptable to commit documentation, metadata templates, command recipes, and manually written example snippets that do not include media.

## Recommended local directory layout

Use a local directory outside the repository, for example:

```text
/Users/kengo/tmp/guitar-tab-agent-golden/
  audio/
    input2.wav
  metadata/
    input2.json
  outputs/
    input2.notes.json
    input2.tab.txt
  logs/
```

The exact path is local-only and should not be assumed by tests.

## Intended fingering shorthand

Do not require hand-written ASCII TAB as the first input. For local golden clips, the easiest source-of-truth notation should be a compact string/fret shorthand.

Use this form:

```text
<string>s-<fret>f
```

Examples:

```text
1s-2f
1s-4f
2s-5f
6s-0f
```

Meaning:

- `1s` means 1st string, the high E string in standard guitar TAB notation.
- `6s` means 6th string, the low E string.
- `0f` means open string.
- `2f` means 2nd fret.

For a monophonic phrase, write comma-separated events in chronological order:

```text
1s-2f, 1s-4f, 1s-6f, 1s-7f
```

For notes that are intentionally separated by a pause, insert `rest`:

```text
1s-2f, 1s-4f, rest, 1s-6f, 1s-7f
```

For uncertain notes, use `?` only when the take is still useful but the exact intended fingering is unclear:

```text
1s-2f, 1s-4f, ?, 1s-7f
```

A clip with too many `?` entries should remain `candidate` or become `rejected`; it should not become `known_good`.

### Optional rhythm hints

Rhythm does not need to be encoded at first. If needed, add a plain-language note such as:

```text
slow even eighth notes, no intentional rests
```

or:

```text
played freely, with a short pause after the fourth note
```

Do not overfit the metadata format before it is needed.

## Clip metadata template

For each local clip, write a small metadata file before judging model output.

Example: `metadata/input2.json`

```json
{
  "clip_id": "input2",
  "audio_path": "../audio/input2.wav",
  "status": "candidate",
  "recorded_by": "kengo",
  "recording_date": "2026-06-25",
  "instrument": "electric guitar",
  "tuning": "E standard",
  "recording_chain": "local user recording",
  "input_class": "clean monophonic guitar-forward",
  "tempo_bpm": null,
  "phrase_type": "unknown",
  "intended_description": "TODO: describe what was played before evaluating output",
  "intended_fingering_shorthand": "TODO: e.g. 1s-2f, 1s-4f, 1s-6f",
  "intended_tab": null,
  "expected_properties": {
    "mostly_monophonic": true,
    "no_background_band": true,
    "no_chords": true,
    "no_bends": true,
    "no_slides": true
  },
  "notes": [
    "Do not commit the audio or generated outputs.",
    "Use this as a local candidate until the phrase and intended fingering are documented."
  ]
}
```

The `intended_fingering_shorthand` field is the primary human-authored reference for early local clips. `intended_tab` may be left `null` until a later step converts or rewrites the shorthand into ASCII TAB.

## Example metadata using shorthand

If the clip is a simple high-E-string phrase on frets 2, 4, 6, and 7, write:

```json
{
  "clip_id": "input2",
  "audio_path": "../audio/input2.wav",
  "status": "documented",
  "recorded_by": "kengo",
  "recording_date": "2026-06-25",
  "instrument": "electric guitar",
  "tuning": "E standard",
  "recording_chain": "local user recording",
  "input_class": "clean monophonic guitar-forward",
  "tempo_bpm": null,
  "phrase_type": "one_string_phrase",
  "intended_description": "Played a clean monophonic phrase on the 1st string using frets 2, 4, 6, and 7.",
  "intended_fingering_shorthand": "1s-2f, 1s-4f, 1s-6f, 1s-7f",
  "intended_tab": null,
  "expected_properties": {
    "mostly_monophonic": true,
    "no_background_band": true,
    "no_chords": true,
    "no_bends": true,
    "no_slides": true
  },
  "notes": [
    "Use shorthand as the source of intended fingering."
  ]
}
```

## Initial candidate: `input2.wav`

Treat `input2.wav` as a local golden-set candidate, not as an official smoke checkpoint yet.

Before running or judging the tool output, record:

1. what phrase was played
2. approximate tempo if known
3. intended string/fret positions using shorthand
4. whether there are mistakes, pauses, dead notes, noise, or string squeaks
5. optional ASCII TAB, only if easy to write

This prevents the evaluation from becoming retrospective or biased by the model output.

## Suggested phrase ladder

Build the local golden set gradually. Start with short clips, roughly 5-15 seconds each.

### G0: Current candidate

- `input2.wav`
- Document what was played using shorthand.
- Decide later whether it should become a known-good checkpoint.

### G1: One-string chromatic phrase

Purpose: basic pitch extraction and note ordering.

Example shorthand:

```text
1s-5f, 1s-6f, 1s-7f, 1s-8f
```

### G2: Across-string chromatic phrase

Purpose: check string/fret ambiguity across adjacent strings.

Example shorthand:

```text
1s-5f, 1s-6f, 1s-7f, 1s-8f, 2s-5f, 2s-6f, 2s-7f, 2s-8f
```

### G3: One-position major scale

Purpose: check natural single-note phrase behavior within a position box.

Example shorthand:

```text
5s-3f, 5s-5f, 4s-2f, 4s-3f, 4s-5f, 3s-2f, 3s-4f, 3s-5f
```

### G4: Pentatonic lick

Purpose: check a more guitar-like monophonic phrase.

Example shorthand:

```text
1s-5f, 1s-8f, 2s-5f, 2s-8f, 3s-5f, 3s-7f
```

### G5: Same-pitch different-string ambiguity

Purpose: stress the decoder's string/fret choice.

Example shorthand:

```text
1s-5f, 2s-10f
```

Both notes are the same pitch in standard tuning. The metadata should preserve the intended fingering so that audio-only ambiguity is visible.

### G6: Position-shift phrase

Purpose: test ergonomic position continuity and deliberate shifts.

Example shorthand:

```text
1s-5f, 1s-7f, 1s-8f, 1s-10f, 1s-12f
```

### G7: Repeated-note phrase

Purpose: test repeated-note stability and unintended string switching.

Example shorthand:

```text
2s-5f, 2s-5f, 2s-5f, 2s-5f
```

### G8: Tempo variants

Purpose: test robustness to timing density.

Record the same shorthand sequence as slow and medium takes.

## Running local evaluation

From the repository root, keep outputs outside the repository or under a local ignored scratch path.

Example using `input2.wav`:

```bash
mkdir -p /Users/kengo/tmp/guitar-tab-agent-golden/outputs

uv run tabgen audio-to-notes \
  /Users/kengo/tmp/guitar-tab-agent-golden/audio/input2.wav \
  --min-confidence 0.2 \
  --min-duration 0.03 \
  --out /Users/kengo/tmp/guitar-tab-agent-golden/outputs/input2.notes.json

uv run tabgen audio-to-tab \
  /Users/kengo/tmp/guitar-tab-agent-golden/audio/input2.wav \
  --min-confidence 0.2 \
  --min-duration 0.03 \
  > /Users/kengo/tmp/guitar-tab-agent-golden/outputs/input2.tab.txt
```

If the local web UI is being checked:

```bash
uv run tabgen web --host 127.0.0.1 --port 8765
```

Then upload `input2.wav` through the browser and compare the displayed TAB with the intended fingering shorthand.

## What to inspect

Do not judge only by exact TAB equality. Early evaluation should inspect:

- number of recovered notes
- chronological ordering
- obvious pitch mistakes
- missing notes
- spurious short notes
- whether the TAB stays near the intended position
- whether the decoder escapes to open strings or low frets unexpectedly
- whether the output is still a playable/editable draft

For ambiguous cases, record both:

- intended fingering shorthand
- generated TAB

and mark whether the difference is acceptable, ambiguous, or wrong.

## Candidate status levels

Use these statuses in local metadata:

- `candidate`: newly recorded, not yet interpreted
- `documented`: phrase and intended fingering shorthand are written down
- `usable`: output is informative for development, even if imperfect
- `known_good`: stable enough to reference in a smoke checkpoint
- `rejected`: bad recording, wrong take, unclear intent, or not useful

Only promote a clip to `known_good` when:

1. the intended phrase is documented before final judgment
2. the recording is clean enough for the current MVP scope
3. the generated output is stable enough to be useful
4. the clip tests a distinct behavior not already covered
5. the clip can be rerun locally without committing media

## External datasets

External datasets should be treated as second-stage benchmarks.

They may be useful later for generalization, robustness, or research comparison, but they should not replace the local golden set because they add extra uncertainty around licensing, recording conditions, annotation format, playing style, and ground-truth interpretation.

Before using an external dataset, create a separate issue that documents:

- license and redistribution constraints
- whether audio and TAB/fingering annotations are both available
- expected format conversion
- whether files can be used locally only
- whether derived artifacts can be committed
- what specific product question the dataset answers

## Related docs

- `docs/audio_only_mvp.md`
- `docs/audio_only_smoke_checkpoint.md`
- `docs/local_web_smoke_checkpoint.md`
- `docs/future_backlog.md`
