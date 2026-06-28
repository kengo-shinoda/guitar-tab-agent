# Contributing

Thank you for your interest in contributing to `guitar-tab-agent`.

This project is currently an early local-first audio-to-TAB draft generator. The
most useful contributions are small, well-scoped changes that improve the
reproducibility, transparency, and usability of the current MVP.

## Current project scope

The current public MVP focuses on:

- standard 6-string guitar
- standard tuning
- short, clean guitar audio
- monophonic or mostly single-note phrases
- local-first CLI and local browser workflows
- playable, editable TAB drafts rather than exact ground-truth fingering

Please keep contributions aligned with this scope unless an issue explicitly
states otherwise.

## Non-goals for current MVP contributions

Please do not open pull requests that broaden the MVP to any of the following
without prior discussion in an issue:

- arbitrary YouTube, streaming-service, or web-video ingestion
- full-song transcription
- dense polyphonic guitar transcription
- exact notation for bends, slides, vibrato, hammer-ons, or pull-offs
- source separation as a required dependency
- custom tunings, bass guitar, 7-string guitar, or other instruments
- production hosted service, account, billing, or social sharing features

These may become future work, but they are intentionally outside the current
public MVP path.

## Development setup

Install project and development dependencies:

```bash
uv sync --dev
```

Run the test suite:

```bash
uv run pytest
```

Inspect the CLI:

```bash
uv run tabgen --help
```

Real audio transcription commands require the optional Basic Pitch dependency:

```bash
uv pip install basic-pitch
```

Commands that operate on existing JSON or synthetic note events can be used
without Basic Pitch.

## Good first contributions

Good first contributions include:

- documentation improvements
- small tests for TAB rendering, candidate generation, or decoder behavior
- local web UI usability fixes
- clearer error messages
- safe demo workflows using owned, generated, public-domain, or properly
  licensed material
- issue reproduction notes with minimal examples

## Demo and test material policy

Do not commit copyrighted third-party audio or video fixtures unless the license
explicitly permits redistribution in this repository.

Prefer:

- synthetic test data
- short self-recorded audio created for this project
- public-domain material
- material with clear redistribution rights

When in doubt, do not commit the media file. Instead, describe how to reproduce
the example locally.

## Pull request expectations

A good pull request should:

- be small enough to review
- explain the user-facing or maintainer-facing reason for the change
- include tests when behavior changes
- keep the README and docs consistent with the current MVP scope
- avoid adding heavy dependencies unless the issue explicitly justifies them
- keep local-first behavior working

For changes to decoder scoring or TAB output, please include before/after
examples or a short explanation of the affected case.
