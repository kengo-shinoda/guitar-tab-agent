# Prioritized Future Backlog

This document is the single source of truth for larger future product ideas that should not be turned into immediate implementation issues yet.

The guiding principle is:

> Solve as much as possible with audio first. Use video only for residual ambiguity that audio and playability constraints cannot resolve reliably.

In other words, video is not the default MVP dependency. It is the late-stage disambiguation signal for cases where audio-only inference remains underdetermined or too noisy.

## Current baseline

The current product focus is still the audio-only local MVP:

- clean guitar-forward input
- mostly monophonic or single-note phrases
- no background band, vocals, drums, or environmental noise
- standard 6-string guitar
- standard tuning
- Basic Pitch note events
- chronological filtering/sorting
- ergonomic string/fret decoding
- ASCII TAB draft output

The product promise remains: generate a playable, editable TAB draft, not a guaranteed ground-truth fingering transcription.

## Priority ladder

### P0: Keep the current audio-only MVP stable

Status: current focus.

Goal: preserve a simple and reliable known-good path:

```text
audio -> NoteEvents -> ergonomic string/fret decoder -> ASCII TAB
```

Representative work:

- keep CLI and local web UI stable
- keep workflows reusable across CLI/web/future interfaces
- document smoke checkpoints
- improve errors and user-facing limitations
- avoid broad refactors and premature feature expansion

Do not add video, chord support, source separation, or notation-editor complexity in P0.

### P1: Improve audio-only robustness for clean monophonic guitar

Status: near future.

Goal: make the current target use case more reliable before expanding the input domain.

Representative work:

- better NoteEvent filtering defaults
- clearer confidence thresholds
- duration/pitch-range presets for guitar
- better note cleanup before decoding
- optional decoder debug JSON
- better UI feedback for failed or low-confidence transcription
- small synthetic or self-generated smoke fixtures

This remains single-note / mostly monophonic and guitar-forward.

### P2: Handle less ideal audio while remaining guitar-forward

Status: future.

Goal: relax the clean-audio assumption without jumping directly to full band transcription.

Representative input expansion:

- mild room noise
- imperfect recording levels
- small amounts of string noise
- light effects that do not destroy pitch tracking
- short phrases with occasional ambiguous onsets

Representative work:

- more robust note post-processing
- confidence-aware TAB output
- warnings for low-confidence segments
- review markers around uncertain notes
- better fallback behavior when audio confidence is poor

Still out of scope here:

- dense polyphony
- full band mixes
- source separation
- video evidence

### P3: Expand audio-only decoding toward limited polyphony and simple chords

Status: future, after audio-only monophonic quality is solid.

Goal: support the simplest useful harmonic cases without claiming full guitar transcription.

Representative scope:

- double-stops
- sparse dyads
- simple triads when note events are clear
- arpeggiated patterns that are close to monophonic
- chord-like clusters with strong confidence

Representative work:

- represent simultaneous or near-simultaneous NoteEvents
- generate multiple string/fret assignments per time slice
- add chord voicing cost terms
- prevent physically impossible left-hand shapes
- emit uncertainty when multiple voicings remain plausible

Important constraint: chord support should not destabilize the monophonic path.

### P4: Address stronger audio ambiguity before using video

Status: future.

Goal: push audio-only inference as far as reasonably possible before relying on video.

Representative scope:

- stronger pitch ambiguity
- missed or spurious notes
- overlapping harmonics
- moderate effects
- passages where several string/fret paths remain similarly plausible

Representative work:

- sequence-level confidence scoring
- explicit ambiguity reporting
- alternative TAB hypotheses
- top-k decoding paths
- confidence-weighted review output
- optional source-separation experiments only if justified by evidence

This phase decides which ambiguity classes are truly unsolvable from audio alone.

### P5: Use video as residual ambiguity resolver

Status: future; original long-term design motivation.

Goal: use left-hand video evidence to collapse the remaining string/fret degeneracy after audio-only and ergonomic constraints have done as much as they can.

Core philosophy:

```text
audio proposes notes and candidate TAB paths
playability narrows the paths
video resolves the remaining fingering ambiguity
```

Representative scope:

- left-hand position evidence
- visible fret-region likelihood
- manual or semi-automatic fretboard calibration
- mapping image-space hand landmarks to approximate fret positions
- using video to choose among audio-plausible string/fret candidates

Representative work:

- robust manual fretboard calibration
- calibration smoke tests
- timestamp alignment between audio and frames
- left-hand likelihood from calibrated landmarks
- decoder integration that treats video as evidence, not absolute truth
- confidence and disagreement reporting when audio/video conflict

Important constraint: video should not become a required dependency for the core audio-only product path.

### P6: Advanced video-assisted transcription

Status: long-term future.

Goal: move beyond left-hand disambiguation toward richer video evidence.

Representative work:

- right-hand picking/plucking evidence
- string activity evidence
- better fretboard tracking under perspective and motion
- handling partial occlusion
- synchronized visual review UI
- video-assisted correction workflow
- dataset collection from corrected user sessions

This is not part of the near-term public MVP.

### P7: Broader product/export/editor expansion

Status: long-term future.

Goal: turn the transcription engine into a broader notation product once the inference core is credible.

Representative work:

- interactive TAB editor
- correction workflow
- MusicXML export
- Guitar Pro export if legally and technically appropriate
- project save/load
- user-managed examples
- custom tunings
- 7-string guitar
- bass support
- deployment or packaging beyond local-first use

These should come after the core transcription and uncertainty model are mature.

## How to promote a future item into an active issue

A future item should become an open implementation issue only when all of the following are true:

1. The current MVP path is not being destabilized.
2. The task can be scoped into a small reviewable PR.
3. The acceptance criteria are concrete.
4. The task does not require committing copyrighted media or large generated artifacts.
5. The task has a clear test strategy, smoke recipe, or documentation-only validation path.
6. The task respects `AGENTS.md` constraints.

## Current do-not-start list

Do not ask Codex to implement these directly without a smaller scoping issue first:

- full chord transcription
- dense polyphonic guitar transcription
- full-band transcription
- automatic source separation
- fully automatic video fretboard tracing
- right-hand evidence
- custom model training
- MusicXML or Guitar Pro export
- full notation editor
- cloud deployment
- 7-string, bass, or arbitrary custom tuning support

These ideas are intentionally preserved here so they are not forgotten, but they are not immediate implementation tasks.
