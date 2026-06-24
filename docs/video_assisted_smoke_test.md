# Video-Assisted Smoke Test Recipe

This recipe documents the manual video-assisted smoke workflow for comparing
audio-only TAB output against TAB output constrained by left-hand fret
likelihood JSON.

The manual likelihood file is an interim stand-in for future
`HandLandmarkFrame`-derived likelihood. This is not full video end-to-end
transcription yet, and no real recordings, generated note JSON, generated TAB,
plots, or notebook outputs should be committed.

## 1. Update The Local Environment

Start from the latest `main` branch and refresh the local environment:

```bash
git switch main
git pull --ff-only origin main
uv sync
uv run pytest
uv run tabgen --help
```

Use local smoke-test files outside the repository, or keep them untracked and
delete them after the run.

## 2. Generate Filtered Notes From Audio

Run Basic Pitch through the existing CLI and apply the current useful filters
for standard six-string guitar:

```bash
tabgen audio-to-notes input.wav \
  --min-confidence 0.55 \
  --min-pitch 40 \
  --max-pitch 88 \
  --out notes.filtered.json
```

`notes.filtered.json` is a generated smoke artifact. Do not commit it.

## 3. Create Manual Chronological Likelihood

Create a manual left-hand likelihood file from the filtered notes. Chronological
ordering matters because `NoteEvent` JSON may not be sorted by `start`, while
the manual evidence pattern should follow performance time.

This simple smoke recipe cycles through frets 9, 10, 11, and 12 in chronological
note order:

```bash
python - <<'PY'
import json
from pathlib import Path

notes_path = Path("notes.filtered.json")
out_path = Path("left_hand_likelihood.manual.chronological.json")

notes = json.loads(notes_path.read_text())
target_frets = [9, 10, 11, 12]

notes_by_time = sorted(notes, key=lambda n: n["start"])

records = []
for i, note in enumerate(notes_by_time):
    fret = target_frets[i % len(target_frets)]
    records.append({
        "time": note["start"],
        "likelihood": {str(fret): 1.0}
    })

out_path.write_text(json.dumps(records, indent=2))
print(f"Wrote {out_path} with {len(records)} records")
PY
```

`left_hand_likelihood.manual.chronological.json` is also a generated smoke
artifact. Do not commit it.

## 4. Compare Audio-Only And Assisted TAB

Render the audio-only baseline:

```bash
tabgen notes-to-tab notes.filtered.json \
  --out tab.audio_only.txt
```

Render the same notes with manual left-hand fret likelihood evidence:

```bash
tabgen notes-to-tab notes.filtered.json \
  --left-hand-likelihood left_hand_likelihood.manual.chronological.json \
  --left-hand-weight 10 \
  --out tab.left_hand_assisted_chronological.txt
```

Both TAB files are generated smoke artifacts. Do not commit them.

## 5. Expected Qualitative Result

The audio-only output may collapse ambiguous phrases onto first/second-string
low or open positions, for example:

```text
e|----------9-10-11--12-4--5-6--7-0-1--2-3----------
B|------------------------------------------0-1--2-3
G|--------------------------------------------------
D|--------------------------------------------------
A|--------------------------------------------------
E|--------------------------------------------------
```

With chronological manual left-hand likelihood evidence, the ambiguous phrases
should move toward the intended 9-12f positions on lower strings:

```text
e|----------9-10-11--12--------------------------------------
B|----------------------9--10-11--12-------------------------
G|-----------------------------------9-10--11-12-------------
D|------------------------------------------------9-10--11-12
A|-----------------------------------------------------------
E|-----------------------------------------------------------
```

This smoke test validates the current manual evidence path:

- `audio-to-notes` produces filtered `NoteEvent` JSON.
- Manual chronological likelihood provides fret evidence over frets 1..max_fret.
- `notes-to-tab --left-hand-likelihood` passes that evidence into the decoder.
- The renderer produces a deterministic ASCII TAB comparison.

Future video work should replace the manual likelihood JSON with likelihood
derived from calibrated `HandLandmarkFrame` data.
