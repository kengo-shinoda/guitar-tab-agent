# Audio-Only Smoke Checkpoint

## Purpose

This page records the current known-good audio-only smoke checkpoint before the
next development step. It captures a successful local end-to-end run from clean
monophonic guitar audio to a playable ASCII TAB draft.

Known-good main commit:

- `8853f5a48b56f94f8c4b3e8caa1c1316ae08aa78`
- `Sort NoteEvents chronologically before TAB decoding`

This checkpoint follows the merged fixes from:

- PR #52: sequence-level ergonomic fingering path decoder.
- PR #54: 4-fret position-box continuity in the decoder.
- PR #58: chronological `NoteEvent` sorting before JSON export and TAB decoding.

## Local Smoke Environment

- Development repo: `/Users/kengo/Documents/guitar-tab-agent`
- Smoke directory: `/Users/kengo/tmp/guitar-tab-agent-smoke`
- Smoke input audio: `input.wav`

The smoke audio and generated outputs are local-only artifacts. Do not commit
`input.wav`, `notes.after58.json`, `tab.after58.txt`, or other generated smoke
files.

## Command Sequence

From the development repo:

```bash
cd /Users/kengo/Documents/guitar-tab-agent
git switch main
git pull --ff-only origin main
uv sync
uv run pytest
uv run tabgen --help
```

From the local smoke directory:

```bash
cd /Users/kengo/tmp/guitar-tab-agent-smoke

/Users/kengo/Documents/guitar-tab-agent/.venv/bin/tabgen audio-to-notes input.wav \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88 \
  --out notes.after58.json

/Users/kengo/Documents/guitar-tab-agent/.venv/bin/tabgen audio-to-tab input.wav \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88 \
  --out tab.after58.txt
```

Optional local inspection:

```bash
python - <<'PY'
import json

notes = json.load(open("notes.after58.json"))
print("num notes:", len(notes))
print("midi:", [note["pitch_midi"] for note in notes])
print("starts:", [round(note["start"], 3) for note in notes])
print(
    "chronologically sorted:",
    notes == sorted(notes, key=lambda n: (n["start"], n["end"], n["pitch_midi"])),
)
print(open("tab.after58.txt").read())
PY
```

## Observed Notes

- `num notes: 16`
- MIDI sequence:
  `[73, 74, 75, 76, 68, 69, 70, 71, 64, 65, 66, 67, 59, 60, 61, 62]`
- Starts:
  `[2.428, 3.055, 3.566, 4.159, 4.797, 5.413, 6.041, 6.691, 7.283, 7.841, 8.457, 9.084, 9.688, 10.328, 10.931, 11.582]`
- `chronologically sorted: True`

## Observed TAB

```text
e|----------9-10-11--12--------------------------------------
B|----------------------9--10-11--12-------------------------
G|-----------------------------------9-10--11-12-------------
D|------------------------------------------------9-10--11-12
A|-----------------------------------------------------------
E|-----------------------------------------------------------
```

## Interpretation

- Basic Pitch can recover this clean monophonic phrase as the expected MIDI
  sequence.
- The `NoteEvent` pipeline sorts extracted notes chronologically.
- The ergonomic decoder preserves the 9-12 position box across adjacent strings.
- `audio-to-tab` can produce the expected playable TAB draft directly from
  `input.wav`.

## Limitations

- This is a local smoke checkpoint, not a committed test fixture.
- Do not commit `input.wav`, `notes.after58.json`, `tab.after58.txt`, or other
  generated smoke artifacts.
- This does not claim general correctness for chords, bends, distortion,
  polyphonic guitar, or full-song transcription.
