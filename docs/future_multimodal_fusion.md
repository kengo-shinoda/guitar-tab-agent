# Future Multimodal Fusion Design

This note documents future architecture guidance. It does not change the
current MVP scope or runtime behavior.

The immediate roadmap still prioritizes monophonic, clean, guitar-only
audio/video input, automatic left-hand likelihood generation, and deterministic
TAB output for standard six-string guitar.

## Current Design

The current implementation is intentionally audio-primary:

- Audio transcription produces `NoteEvent` records as the primary event stream.
- Pitch-compatible string/fret candidates are generated from those notes.
- Left-hand fret likelihood optionally constrains candidate selection to help
  resolve string/fret ambiguity.

This is acceptable for the MVP. It keeps the pipeline testable and lets the
project prove the local CLI workflow before adding broader multimodal logic.

## Future Direction

Future versions should treat audio and video as complementary evidence streams,
not as a strict hierarchy where audio is always ground truth and video is only a
weak helper. Video evidence should eventually be able to validate, correct, or
supplement uncertain audio events.

Audio uncertainty may come from:

- chords and polyphony;
- distortion, noise, or room reflections;
- non-guitar sounds;
- weak or ambiguous onsets;
- missed notes;
- low-confidence pitch detection.

The future fusion layer should represent those uncertainties explicitly so the
decoder can make inspectable decisions when evidence conflicts.

## Possible Evidence Streams

Future evidence streams may include:

- `AudioEvidence`: pitch candidates, onset confidence, duration confidence,
  noise/non-guitar confidence, and polyphony confidence.
- `LeftHandEvidence`: fret likelihood, position confidence, and possible
  string/fret constraints from calibrated fretboard coordinates.
- `RightHandEvidence`: picking or strumming likelihood, onset evidence, and
  string activation likelihood.

These structures should remain decoupled from any specific model output. Model
or library-specific data should stay inside adapter modules.

## Decoder Direction

The future decoder should avoid assuming that audio-derived notes are always
ground truth. It should be able to:

- preserve deterministic behavior where possible;
- expose inspectable score components;
- revise low-confidence or missing audio events when strong video evidence
  supports doing so;
- combine audio, left-hand, and right-hand evidence without hiding conflicts;
- emit warnings or review markers when evidence is ambiguous.

This does not require immediately adopting Viterbi, beam search, or learned
models. A small deterministic decoder with explicit score components remains a
good stepping stone.

## Scope Boundaries

This design note is future guidance only. It does not implement:

- chords or polyphonic TAB decoding;
- distortion, noise, or non-guitar handling;
- source separation;
- right-hand evidence;
- tapping logic;
- left-handed player support;
- decoder behavior changes;
- CLI behavior changes;
- new dependencies;
- real media files or generated artifacts.
