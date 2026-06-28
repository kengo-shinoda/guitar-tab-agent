# Codex for OSS maintenance plan

This document summarizes how `guitar-tab-agent` could use Codex for OSS support.
It is intended to support the public OSS alpha plan and the Codex for OSS
application.

## Project summary

`guitar-tab-agent` is a local-first audio-to-TAB draft generator for short,
clean guitar phrases.

The current MVP takes short guitar audio, extracts note-like events, decodes
them into multiple playable TAB candidates, and lets the user compare, select,
play back, copy, and download a result. The generated TAB is a playable and
editable draft, not exact ground-truth fingering.

## Why this project matters

Guitar TAB generation is not just generic pitch transcription. The same pitch
can usually be played on multiple string/fret positions, so audio alone cannot
reliably determine the exact fingering used by a player.

This project treats that ambiguity as a first-class product and engineering
constraint. Instead of claiming blind automatic fingering reconstruction, it
provides multiple TAB candidates for human review and correction.

This makes the project useful as an open-source foundation for:

- local-first music tooling
- transparent audio-to-TAB draft generation
- human-in-the-loop creative AI workflows
- guitar education and practice tools
- reproducible experiments around fingering ambiguity and ergonomic decoding

## Current OSS goals

The near-term OSS goals are:

1. Keep the audio-only local MVP reproducible.
2. Document the current scope and limitations clearly.
3. Avoid copyrighted or unclear demo fixtures.
4. Improve candidate review and playback workflows.
5. Add phrase-level position guidance without hiding decoder behavior.
6. Keep decoder scoring transparent and testable.
7. Preserve local-first operation as the default development and demo path.

## Current technical scope

The current public MVP is intentionally narrow:

- standard 6-string guitar
- standard tuning
- short clips, roughly 10-30 seconds
- clean guitar-forward audio
- monophonic or mostly single-note phrases
- local CLI and local browser workflows
- editable ASCII TAB drafts and intermediate event data

The project does not currently claim support for:

- full-song transcription
- exact observed fingering reconstruction
- arbitrary YouTube or web video ingestion
- robust dense polyphonic guitar transcription
- production hosted service deployment
- broad notation export or full notation editing
- custom tunings, bass guitar, or 7-string guitar

## How Codex would help

Codex support would be most useful for maintainer workflows rather than for
making unsupported product claims.

### Issue triage

Codex could help classify incoming issues by area:

- audio
- decoder
- TAB rendering
- local web UI
- documentation
- tests
- security/privacy
- future video evidence

It could also help identify whether an issue belongs to the current MVP or
should be labeled as future work.

### Pull request review

Codex could help review pull requests for:

- scope creep beyond the current audio-only MVP
- changes that break local-first assumptions
- decoder scoring changes without tests or before/after examples
- TAB rendering regressions
- unsafe demo media additions
- README/docs drift from the current product positioning
- accidental introduction of heavy required dependencies

### Regression and smoke-test assistance

Codex could help maintain compact smoke-test reports for:

- CLI command behavior
- local web UI startup
- candidate generation
- ASCII TAB rendering
- selected candidate playback payloads
- documentation examples

### Release workflows

Codex could help maintain release checklists for public alpha releases:

- README and limitations review
- dependency and license review
- safe demo material review
- CI status review
- changelog and release note drafting
- public-facing wording review to avoid overclaiming transcription quality

### Security and privacy review

Because the local web UI accepts user audio, Codex could help review changes
around:

- upload handling
- temporary file cleanup
- path handling
- local server binding behavior
- storage assumptions
- public deployment warnings
- user-submitted media policy

## API credit usage plan

API credits would be used for maintainer automation and review workflows, not
for hosting a public transcription service.

Potential uses include:

- summarizing issues and PRs for maintainer review
- drafting release notes from merged PRs
- generating documentation updates from accepted design decisions
- reviewing PR diffs for scope, test coverage, and documentation drift
- producing smoke-test summaries from CI logs
- improving contributor-facing documentation

## Why Codex is a good fit

This repository is intentionally structured for incremental, reviewable work.
The project benefits from small PRs, explicit scope boundaries, transparent
decoder behavior, and careful documentation.

Codex is a good fit because the hard maintenance problem is not simply writing
more code. The harder problem is keeping the OSS project honest about its
limitations while gradually improving the candidate-based TAB drafting workflow.

## Near-term milestones

Suggested public alpha milestones:

1. Public OSS alpha readiness
   - license, contribution, security, and public README cleanup
   - safe demo material policy
   - CI and release checklist

2. Candidate review workflow
   - faster candidate audition
   - clearer candidate metadata
   - better playback workflow

3. Preferred position hints
   - open, 3rd, 5th, 7th, 9th, and 12th position hints
   - soft penalties for candidates outside the preferred position
   - CLI and local web UI exposure

4. Minimal correction workflow
   - edit selected string/fret assignments
   - export corrected TAB
   - preserve correction examples for regression tests

## Application positioning

The application should position this project as a small but focused OSS project
for local-first, human-in-the-loop music tooling.

The strongest claim is not that the project solves perfect automatic guitar
transcription. The stronger and more accurate claim is that it exposes guitar
TAB ambiguity, generates editable candidates quickly, and keeps the guitarist in
control of the final result.
