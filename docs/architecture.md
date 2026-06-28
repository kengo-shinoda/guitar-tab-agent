# Architecture

## 1. System Overview

The public-alpha system generates editable guitar TAB drafts from short, clean guitar audio. It combines audio-derived note events, guitar-specific string/fret candidate generation, playability constraints, ergonomic scoring, and human review.

Video-assisted evidence is future work. The architecture keeps video, calibration, and hand-evidence modules decoupled so future releases can add left-hand and fretboard evidence without changing the audio-only public MVP claim.

The architecture is intentionally modular so coding agents can work on one layer at a time without changing the full pipeline. Each module owns clear inputs, outputs, and failure modes. Early versions should use simple deterministic logic before introducing more complex decoders or model integrations.

Primary modules:

- `audio`: produces `NoteEvent` records from local audio files.
- `fusion`: selects string/fret positions from audio notes, optional evidence, and playability constraints.
- `tab rendering`: exports JSON and ASCII TAB first.
- `CLI`: exposes pipeline steps through the `tabgen` command for local development and batch use.
- `local web UI`: supports local audio upload, candidate preview, and TAB copy/download.
- `video`: future module for time-aligned visual evidence such as fretboard calibration and hand landmarks.

Source layout:

```text
src/guitar_tab_agent/
  audio/      audio-to-note adapters and note filtering
  video/      future frame extraction, calibration, and hand tracking
  fusion/     string/fret candidate generation, scoring, and decoding
  tab/        ASCII TAB rendering and later export adapters
  web/        minimal local audio-to-TAB UI
  cli.py      implementation for the `tabgen` command
  schema.py   canonical shared dataclasses
  models.py   compatibility wrappers for early skeleton APIs
```

The Python package is `guitar_tab_agent`. The CLI command is `tabgen`; do not rename the package to `tabgen`.

## 2. Data Flow

Current public-alpha audio-only flow:

```text
input audio
  |
  +-- audio module
  |     |
  |     +-- audio-to-note adapter
  |     +-- note filtering and chronological sorting
  |     +-- NoteEvent[]
  |
  +-- fusion module
  |     |
  |     +-- pitch-to-string/fret candidates
  |     +-- ergonomic scoring
  |     +-- optional first-position and left-hand-likelihood hints
  |     +-- ranked candidate decoder
  |     +-- DecodedTabEvent[]
  |
  +-- tab rendering
        |
        +-- JSON output
        +-- ASCII TAB output
        +-- ranked TAB candidates for review
```

Future multimodal flow:

```text
input video or time-aligned frame data
  |
  +-- video module
  |     |
  |     +-- frame extraction
  |     +-- manual fretboard calibration
  |     +-- hand landmark detection
  |     +-- time-aligned VideoEvidence[]
  |
  +-- fusion module
        |
        +-- combine audio pitch constraints, visual evidence, and playability costs
        +-- reduce string/fret ambiguity where visual evidence is reliable
```

Intermediate files should be serializable so later steps can be rerun without repeating expensive extraction. This also makes debugging easier when agents implement modules independently.

## 3. Internal Data Schemas

Schemas should be small, typed, and stable. Dataclasses are enough for the initial implementation; pydantic should not be added unless validation needs justify it.

Canonical shared dataclasses live in `src/guitar_tab_agent/schema.py`. `src/guitar_tab_agent/models.py` may keep temporary compatibility wrappers while early skeleton APIs are migrated.

### `NoteEvent`

Produced by the audio module.

- `start`: note start time in seconds from media start.
- `end`: note end time in seconds from media start.
- `pitch_midi`: MIDI pitch number.
- `confidence`: normalized confidence from 0.0 to 1.0.
- `source`: adapter name, such as `basic_pitch`.

### `FretboardCalibration`

Produced by future manual calibration in the video module.

- `nut_string_6`: optional image-space point.
- `nut_string_1`: optional image-space point.
- `bridge_string_6`: optional image-space point.
- `bridge_string_1`: optional image-space point.
- `timestamp`: optional frame time used for calibration.

Perspective transforms and normalized fretboard mapping are future video-module work, not part of the current audio-only public MVP.

### `HandLandmarkFrame`

Produced by future video hand tracking.

- `timestamp`: frame timestamp.
- `landmarks`: named project-level landmarks as `(name, x, y)` tuples.
- `confidence`: optional detection confidence.

MediaPipe-specific objects must stay inside the video adapter layer.

### `VideoEvidence`

Time-aligned visual evidence consumed by fusion in future multimodal workflows.

- `timestamp_sec`: evidence time.
- `left_hand_likelihood`: optional probability-like scores by string/fret or fret region.
- `right_hand_string_likelihood`: optional probability-like scores by string.
- `calibration_id`: calibration record used for mapping coordinates.
- `warnings`: non-fatal issues such as occlusion or missing landmarks.

### `StringFretCandidate`

Generated by fusion for each note.

- `string`: 1 is high E, 6 is low E.
- `fret`: 0 or greater.
- `pitch_midi`: MIDI pitch produced by this string/fret position.
- `confidence`: optional candidate confidence before decoding.

### `DecodedTabEvent`

Selected output event.

- `start`: event start time in seconds.
- `end`: event end time in seconds.
- `string`: selected guitar string.
- `fret`: selected fret.
- `pitch_midi`: selected MIDI pitch.
- `confidence`: confidence in the selected placement.

Score breakdowns and `needs_review` markers are planned decoder/review-output extensions.

## 4. Future Instrument and Tuning Profiles

Phase 0 and Phase 1 remain fixed to six-string standard-tuning guitar. The current candidate generation, decoder, ASCII renderer, CLI, and local web UI should not claim support for 7-string guitar, bass guitar, or custom tunings yet.

Future support should be introduced through a small `InstrumentProfile` design rather than scattered constants. A profile may eventually describe:

- instrument family, such as guitar or bass;
- string count;
- string labels in display order;
- open-string MIDI pitches for the selected tuning;
- tuning name or user-provided tuning metadata;
- configurable maximum fret;
- validation rules for playable string/fret ranges.

Future profiles may cover standard 6-string guitar, 7-string guitar, 4/5/6-string bass, custom tunings, arbitrary string labels, and different maximum fret limits. This design should be added only when an issue explicitly asks for it and includes tests that protect existing six-string standard-tuning behavior.

Until then, new code may continue to use the current six-string standard-tuning assumptions. However, when a small local abstraction is easy, prefer it over unnecessary hard-coding that would make a later `InstrumentProfile` migration noisy. Do not introduce broad profile plumbing speculatively.

## 5. Module Boundaries

### Audio

Responsibilities:

- Read local audio files.
- Run an audio-to-note adapter.
- Normalize results into `NoteEvent` records.
- Hide tool-specific output formats from the rest of the system.

Initial tools may include Basic Pitch. `ffmpeg` and Demucs can be added later as optional preprocessing steps when the related workflow is explicitly scoped.

### Video

Responsibilities for future multimodal work:

- Extract frames or read frame timestamps.
- Store and load manual fretboard calibration.
- Convert image coordinates into fretboard-relative evidence.
- Produce hand landmarks and likelihoods aligned to media time.

Video evidence is not required for the current public-alpha audio-only path. Future video work can use manual calibration and mocked/synthetic visual evidence before full MediaPipe integration.

### Fusion

Responsibilities:

- Enumerate valid string/fret candidates from each `NoteEvent` under the current six-string standard-tuning MVP constraint.
- Combine pitch constraints, optional left-hand likelihood, optional right-hand likelihood, playability prior, and transition cost.
- Decode one or more ranked sequences of `DecodedTabEvent` records.
- Preserve score breakdowns for debugging and correction.

The initial decoder should be simple and deterministic, such as lowest-cost candidate selection with a basic movement penalty. Later versions can use Viterbi or beam search when transitions and polyphony become more important.

### Tab Rendering

Responsibilities:

- Render selected `DecodedTabEvent` records as ASCII TAB.
- Export machine-readable JSON.
- Keep rendering separate from decoding and scoring.

MusicXML and GuitarPro exports are future work and should consume the same internal `DecodedTabEvent` representation.

### CLI

Responsibilities:

- Provide local commands for pipeline stages.
- Support rerunning individual steps from intermediate JSON files.
- Surface clear errors for unsupported inputs and missing dependencies.

Current public-alpha commands include:

- `tabgen candidates`
- `tabgen notes-to-tab`
- `tabgen audio-to-notes`
- `tabgen audio-to-tab`
- `tabgen web`

Video-related helper commands are experimental/future-facing and should not be described as the public MVP.

### Local Web UI

Responsibilities:

- Upload or select a local audio file.
- Preview generated TAB candidates.
- Copy or download ASCII TAB output.
- Keep uploads local to the user's machine in the default development workflow.

The local web UI should call the same core modules as the CLI rather than duplicating pipeline logic.

### Local-First Frontend and API Integration

The core engine should remain UI-independent. CLI commands, future local API handlers, a local web UI, desktop packaging, and any optional cloud layer should all call the same reusable backend workflows instead of duplicating pipeline logic.

Intended layers:

- Core engine: shared schemas, pitch-to-string/fret candidates, decoder, and TAB renderer.
- Adapters: Basic Pitch, future MediaPipe, `ffmpeg` frame extraction, and other optional dependency boundaries.
- Workflows: reusable orchestration functions such as `audio_to_notes`, `audio_to_tab`, future `video_to_landmarks`, and future `multimodal_to_tab`.
- Interfaces: `tabgen` CLI and local web UI now; later local API and desktop app; optional cloud/API layers only after local quality and UX are validated.

The CLI should stay a thin wrapper around workflow functions. Future frontend or API code should pass user inputs to those workflows and render their outputs, not reimplement note filtering, decoding, rendering, adapter calls, or error handling in UI-specific layers.

Optional dependencies should stay isolated in adapter modules and be imported lazily only when the related feature is requested. This keeps the local CLI and future interfaces usable without installing every audio, video, or ML tool.

The near-term product direction is local-first: CLI and local web UI now, local API later, desktop app packaging after the workflow is useful, and optional cloud/SaaS only after core quality and UX are validated. Mobile/iOS is a future capture companion direction, not the first product target.

Do not commit real audio/video files, generated JSON or TAB outputs, generated plots, or executed notebook outputs. Keep committed fixtures small, deterministic, and human-readable.

## 6. Coordinate Systems

Time coordinates:

- Use seconds from media start as the canonical time base.
- Preserve original frame timestamps when available.
- Align future video evidence to note events by timestamp windows, not by frame index alone.

Image coordinates:

- Use pixel coordinates with origin at the top-left of the source frame.
- `x` increases rightward.
- `y` increases downward.
- Store the source frame dimensions with calibration data.

Manual fretboard calibration:

- Future video work may start with a manually supplied calibration JSON file, not automatic fretboard detection.
- Required points are `nut_string6`, `nut_string1`, `high_fret_string6`, and `high_fret_string1`.
- Each point is an image-space `[x, y]` pixel coordinate.
- The JSON contract stores `video_id`, `frame_time`, `image_width`, `image_height`, and a `points` object containing the four required points.

Fretboard coordinates:

- For the MVP, string numbering follows six-string guitar TAB convention: string 1 is high E, string 6 is low E.
- Fret numbering starts at 0 for open strings.
- Normalized fretboard coordinate `u` runs from the nut toward the bridge/high-fret direction.
- Normalized fretboard coordinate `v` runs from the string 6 side toward the string 1 side.
- Points inside the calibrated quadrilateral should map approximately into `[0, 1] x [0, 1]`.
- Standard tuning MIDI pitches are explicit:
  - string 1: E4, MIDI 64
  - string 2: B3, MIDI 59
  - string 3: G3, MIDI 55
  - string 4: D3, MIDI 50
  - string 5: A2, MIDI 45
  - string 6: E2, MIDI 40
- Future `InstrumentProfile` support should derive labels, open-string pitches, string count, and maximum fret from profile data rather than from this MVP list.

Calibration must record enough orientation metadata to map image-space landmarks to string/fret regions without assuming a fixed left-to-right neck direction.

## 7. Error Handling

Errors should be explicit and recoverable when possible.

- Unsupported tuning or guitar type should fail before decoding.
- Missing external tools should report the tool name and suggested installation path.
- Invalid media files should fail in audio/video extraction, not inside fusion.
- Missing or stale calibration should produce a clear calibration-required error for future video workflows.
- Low-confidence notes or occluded landmarks should become warnings and `needs_review` markers when the pipeline can continue.
- JSON schema version mismatches should produce clear migration or incompatibility messages.

Modules should avoid swallowing errors from external tools. Wrap them with project-specific messages while preserving enough diagnostic detail for debugging.

## 8. Dependency Policy

- Prefer existing OSS tools and pretrained models.
- Keep heavy dependencies behind adapter modules.
- Do not add a dependency until a module needs it.
- Document why each dependency is required, whether it is optional, and how it is tested.
- Unit tests must not require network access, GPU access, or large media files.
- Optional integrations should support graceful skip behavior in tests.

Likely dependency boundaries:

- Basic Pitch: audio-to-note adapter.
- `ffmpeg`: optional media extraction boundary.
- OpenCV: future frame extraction and image handling.
- MediaPipe: future hand landmark detection.
- Demucs: optional future guitar stem separation.

## 9. Testing Strategy

Testing should favor deterministic fixtures and small module boundaries.

- Unit-test pitch-to-string/fret mapping exhaustively for standard tuning.
- Unit-test scoring functions with synthetic candidates.
- Unit-test the initial deterministic decoder with small `NoteEvent` sequences.
- Unit-test ASCII TAB rendering with golden strings.
- Unit-test JSON serialization and schema compatibility.
- Mock external commands and model adapters in unit tests.
- Use tiny synthetic fixtures for calibration and hand landmarks.
- Keep real audio/video integration tests optional and clearly marked.
- Add regression tests for any incorrect fingering, coordinate mapping, or decoding bug.

Each module should be testable without running the full pipeline.

## 10. Future Extensions

- Viterbi or beam search sequence decoding.
- Polyphonic note grouping and chord-aware fingering.
- Preferred-position hints and correction workflows for human-in-the-loop review.
- Right-hand string likelihood from picking-hand video evidence.
- Better left-hand likelihood using MediaPipe landmarks and calibrated fretboard geometry.
- Optional Demucs preprocessing for guitar-forward but noisy recordings.
- Support for bends, slides, hammer-ons, pull-offs, vibrato, harmonics, and tapping.
- `InstrumentProfile` support for alternate tunings, 7-string guitar, bass guitar, arbitrary string labels, and configurable maximum frets.
- MusicXML and GuitarPro export.
- Interactive web UI for calibration, correction, and playback.
- Confidence visualization and human-in-the-loop correction history.
