# Public alpha release checklist

This checklist is for preparing `guitar-tab-agent` for a public OSS alpha
release.

The goal is not to present the project as a complete automatic transcription
system. The goal is to release a clear, reproducible, local-first audio-to-TAB
draft generator with honest limitations and safe demo practices.

## 1. Product framing

Before release, confirm that public-facing text consistently describes the
project as:

- local-first
- audio-only for the current MVP
- focused on short, clean guitar audio
- intended for monophonic or mostly single-note phrases
- generating playable, editable TAB drafts
- candidate-based and human-in-the-loop

Avoid claiming:

- exact ground-truth fingering
- full-song transcription
- arbitrary YouTube or web-video support
- robust polyphonic transcription
- production hosted service readiness
- replacement for full notation editors or commercial TAB platforms

## 2. README and documentation review

Check that the README:

- states the current MVP scope near the top
- explains the same-pitch/different-string ambiguity
- includes the shortest working CLI path
- includes the local web UI command
- links to current-state, roadmap, and release-planning docs
- links to limitations or states limitations directly
- does not overstate video-assisted capabilities

Check that docs remain internally consistent:

- `docs/current_state.md`
- `docs/audio_only_mvp.md`
- `docs/roadmap.md`
- `docs/codex_for_oss_plan.md`

## 3. License and dependency review

Before release:

- confirm the repository license is present
- confirm optional dependencies are documented as optional
- confirm Basic Pitch setup is documented separately from core commands that do
  not require audio transcription
- review whether any dependency license requires NOTICE or attribution handling
- avoid adding large model files or generated artifacts to the repository

## 4. Safe demo material review

Do not commit or redistribute unclear third-party audio or video material.

Allowed demo sources:

- synthetic test data
- self-recorded audio created for this project
- public-domain material
- material with explicit redistribution rights

Avoid:

- copyrighted songs
- arbitrary YouTube clips
- streaming-service audio
- third-party videos with unclear rights
- examples that imply the tool supports any song or full-mix transcription

When in doubt, document reproduction steps instead of committing media files.

## 5. CI and smoke checks

Before tagging a release, confirm:

```bash
uv sync --dev
uv run pytest
uv run tabgen --help
uv run tabgen candidates 64
uv run tabgen notes-to-tab --help
uv run tabgen audio-to-tab --help
uv run tabgen web --help
```

If a demo audio path is included, also check:

```bash
uv pip install basic-pitch
uv run tabgen audio-to-notes input.wav --out notes.json
uv run tabgen audio-to-tab input.wav --out tab.txt
uv run tabgen web --host 127.0.0.1 --port 8765
```

## 6. Local web UI security and privacy review

Before public alpha, confirm or document:

- the local web UI binds to local use by default
- upload size and file type assumptions are understood
- temporary files are handled safely
- filenames cannot cause path traversal
- user audio is not persisted unexpectedly
- the project does not encourage public internet deployment of the local dev UI
- `SECURITY.md` reflects current assumptions

## 7. Issue and contribution readiness

Before making the repository public:

- confirm `CONTRIBUTING.md` exists
- confirm `SECURITY.md` exists
- confirm issue templates exist
- confirm current MVP non-goals are documented
- create or update planning issues for near-term work
- ensure labels and milestones are understandable enough for public triage

## 8. Release notes

A public alpha release should include:

- one-paragraph project summary
- install and quick-start commands
- known-good input constraints
- limitations
- safe demo note
- major implemented capabilities
- immediate next milestones

Suggested title:

```text
v0.1.0-alpha: local-first audio-to-TAB draft MVP
```

## 9. Final public-release check

Before switching the repository to public or tagging an alpha release, verify:

- no API keys, credentials, or private paths are committed
- no copyrighted audio/video fixtures are committed
- README, package metadata, and docs use consistent product wording
- CI passes
- release notes do not overclaim transcription quality
- commercial/mobile/hosted deployment plans remain clearly separated from the
  OSS core
