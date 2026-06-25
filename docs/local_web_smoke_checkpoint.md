# Local Web UI Smoke Checkpoint

## Purpose

This page records the first successful local web UI smoke checkpoint after
merging the minimal audio-to-TAB browser interface. It verifies that the
browser-facing local path can drive the known-good audio-only workflow:

```text
local web UI / POST /generate -> uploaded input.wav -> existing audio-to-TAB workflow -> ASCII TAB JSON response
```

## Merged PR

- PR #63: `Add minimal local web UI for audio-to-TAB`
- Merge commit: `e7b8d8196c6f38e252a35750f96eb243c37b48b6`

## Local Server Command

The local server was started with:

```bash
tabgen web --host 127.0.0.1 --port 8765
```

Before the smoke run, the PR branch checks passed:

```text
rtk uv run pytest -> 173 passed
rtk uv run tabgen --help -> passed
rtk git diff --check -> passed
```

## Request Shape

The smoke test posted local audio bytes to `/generate` using the same basic
audio filters as the CLI smoke path:

```bash
curl -sS \
  -X POST \
  --data-binary @input.wav \
  -H "Content-Type: audio/wav" \
  -H "X-Filename: input.wav" \
  "http://127.0.0.1:8765/generate?min_confidence=0.55&min_pitch=40&max_pitch=88"
```

## Observed JSON Response Shape

The response was JSON and contained a single TAB payload field:

```text
['tab']
```

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

- `tabgen web` can start the local stdlib web UI.
- `/generate` accepts uploaded audio bytes.
- The endpoint returns JSON containing a `tab` field.
- The web path reuses the existing audio-to-TAB workflow.
- The known-good 9-12 across-strings phrase works through the web path.
- The smoke result was `web smoke: OK`.

## Limitations

- This is a local smoke checkpoint, not a committed test fixture.
- Do not commit `input.wav`, generated JSON, generated TAB, logs, or other
  smoke artifacts.
- This does not prove general correctness for chords, bends, distortion, full
  mixes, editing UI, deployment, or video-assisted workflows.
