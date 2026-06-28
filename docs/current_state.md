# Current state handoff

This document summarizes the current product, technical status, and near-term direction of `guitar-tab-agent`.

It is intended as the first document to read before discussing deployment, demos, marketing, product positioning, or the next development tasks.

## Product summary

`guitar-tab-agent` is a local-first guitar TAB draft generator.

The current MVP takes short guitar audio, extracts note-like events, decodes them into multiple playable TAB candidates, and lets the user compare, select, play back, copy, and download the result.

The generated TAB should be treated as a playable/editable draft, not exact ground-truth fingering.

## Current MVP status

The local web UI is already usable for short audio-to-TAB experiments.

Implemented capabilities include:

- local browser UI via `tabgen web`
- short audio upload
- note filtering by confidence, duration, and MIDI pitch range
- top-k TAB candidate generation
- optional first-note position hint, such as `5s-0f`
- optional single-note mode for mostly monophonic phrases
- candidate selection in the web UI
- selected candidate playback
- copy/download of selected TAB
- playback-ready event payloads
- improved ASCII TAB readability for multi-digit frets
- simple ergonomic decoder scoring, including movement costs and soft penalties for very high frets

This is already useful for reducing the burden of making rough TAB drafts from audio, especially when the user is willing to review and correct the result.

## What has improved recently

Recent work changed the MVP from a bare audio-to-TAB CLI/web prototype into an interactive candidate verifier.

Key improvements:

- Top-k TAB candidates are exposed in CLI and web.
- The web UI can select a candidate rather than only showing one output.
- The user can constrain the first playable note to a known string/fret position.
- Single-note mode can suppress near-simultaneous extra detections for monophonic phrases.
- Candidate payloads contain event metadata for playback and later correction UI.
- Selected candidate playback works in the browser.
- TAB display blocks are wider and horizontally scrollable.
- Adjacent multi-digit frets are now spaced more readably.
- Close sequential events are displayed in distinct TAB columns.
- Very high frets, especially 21f+ on non-1st strings, receive soft ergonomic penalties.

## Key lesson learned

Audio-only transcription is useful but not sufficient for human-preferred TAB fingering.

The current system can often extract a plausible pitch/onset sequence. However, the same pitch can usually be played on multiple string/fret positions. Audio alone usually cannot determine which string/fret position a guitarist actually used or would prefer.

Core ambiguity:

- same pitch -> multiple possible string/fret positions

A human guitarist resolves this using context:

- phrase-level hand position
- local fretboard position boxes
- upcoming notes
- string crossing patterns
- open-string preference or avoidance
- economy of motion
- style and player preference
- visual evidence from the left hand when video is available

Recent local penalties improve some obviously awkward candidates, but they do not solve phrase-level fingering naturalness.

## Current limitation

The main remaining bottleneck is not ASCII rendering and not only pitch extraction.

The bottleneck is phrase-level fingering inference.

The current decoder is still mostly a path search over local string/fret candidates. It has useful costs, but it does not yet model a guitarist's hand position as a first-class state over a phrase.

This means the system can produce TAB that is pitch-plausible and playable in isolation, but not the most natural human fingering.

## Product positioning

Recommended positioning:

A local-first tool that turns short guitar audio into playable/editable TAB drafts with multiple candidates for review.

Safe claims:

- helps reduce manual TAB drafting effort
- generates candidate TABs from audio
- supports local review and correction workflows
- useful for short, clean, mostly single-note guitar phrases
- designed for human-in-the-loop editing

Avoid claiming:

- exact ground-truth fingering
- full song transcription
- production-quality automatic TAB
- Soundslice/Songsterr replacement
- arbitrary YouTube/video support
- robust polyphonic guitar transcription
- guaranteed string/fret accuracy from audio alone

## Deployment implications

The current app is best treated as a local-first prototype.

Near-term deployment discussion should focus on:

- local packaging
- reproducible installation
- small demo workflow
- privacy-friendly local processing
- a narrow set of supported input examples
- clear user expectations around draft quality

Avoid building public-facing claims before the correction workflow and demo constraints are clear.

Do not commit or distribute third-party copyrighted audio/video fixtures. Use owned, generated, public-domain, or properly licensed demo material for deployment and marketing examples.

## Marketing implications

The strongest story is not "perfect automatic transcription."

The stronger story is:

Audio-to-TAB is ambiguous. This tool makes the first draft fast, shows alternatives, and keeps the guitarist in control.

Possible positioning angles:

- "from audio to editable TAB draft"
- "candidate-based guitar TAB generation"
- "local-first TAB draft assistant"
- "built for review, not blind automation"
- "designed around the same-pitch/different-string problem"

The key differentiator is acknowledging fingering ambiguity rather than pretending it does not exist.

## Near-term product direction

The next useful product improvements are:

1. Preferred position hints

   Let the user guide the decoder with a phrase-level preferred position, such as open, 3rd, 5th, 7th, 9th, or 12th position.

2. String-region hints

   Let the user indicate a rough string region, such as high strings, middle strings, or low strings.

3. Candidate-level playback improvements

   Make it faster to audition each candidate, not only the selected one.

4. Minimal correction UI

   Allow the user to edit a chosen candidate by changing string/fret assignments.

5. Position-aware phrase-level decoder

   Model hand position as a phrase-level state rather than only scoring each string/fret candidate locally.

6. Video/left-hand evidence

   Eventually use visual left-hand information to reduce same-pitch/different-string ambiguity.

## Near-term technical direction

The next decoder step should not be more constant tuning.

A better next decoder milestone is:

- Add preferred-position hints to candidate decoding.

A scoped implementation could:

- add an optional preferred position parameter
- define position boxes, e.g. open, 3rd, 5th, 7th, 9th, 12th
- add soft penalties for candidates outside the preferred position
- expose the hint in CLI and local web UI
- keep existing first-note hard hint behavior
- preserve top-k candidate output

A later, larger milestone could be:

- Add position-aware phrase-level fingering decoder.

That should explicitly model position state and position shifts over a phrase.

## Non-goals for now

Do not spend more time on broad local penalty tuning unless tied to a specific failing example and test.

Do not treat human-like fingering as purely a rendering problem.

Do not treat audio-only output as ground truth.

Do not clone Soundslice or Songsterr UI yet.

Do not add large media fixtures to the repository.

Do not broaden scope to arbitrary video, YouTube, custom tunings, bass, or 7-string guitar yet.

## Suggested reading order for future chats

1. `docs/current_state.md`
2. `docs/audio_only_mvp.md`
3. `docs/roadmap.md`
4. Issue #93: audio-only limitation for human-playable TAB fingering
5. Recent PRs around candidate selection, playback, rendering, and high-fret penalties

## Current practical value

Even with the fingering ambiguity limitation, the current tool already reduces the effort of making a TAB draft.

The useful workflow is:

1. Upload short guitar audio.
2. Generate multiple candidates.
3. Use first-note and single-note hints where appropriate.
4. Listen to selected candidate playback.
5. Copy/download the closest candidate.
6. Manually correct fingering.

This workflow is valuable enough for private demos and early deployment planning, provided the output is framed as a draft that needs review.
