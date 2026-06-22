# Roadmap

This roadmap keeps the project practical for iterative work by coding agents. Each phase should be small enough to split into reviewable PRs, with tests and clear intermediate outputs.

## Phase 0: Repo Skeleton, Docs, Schemas, CLI, Audio-Only Baseline

### Goal

Create a stable foundation for later audio, video, fusion, and output work. Establish the core data shapes and prove a minimal audio-only path can produce editable TAB-like output from note events.

Phase 0 is limited to six-string standard-tuning guitar.

### Deliverables

- Product requirements, architecture, evaluation, and roadmap docs.
- Root `AGENTS.md` with project rules.
- Python package skeleton under `src/guitar_tab_agent/`.
- Initial internal schemas for `NoteEvent`, `StringFretCandidate`, and `DecodedTabEvent` in `src/guitar_tab_agent/schema.py`.
- `tabgen` CLI skeleton backed by `src/guitar_tab_agent/cli.py`.
- Standard-tuning pitch-to-string/fret candidate generation.
- Basic ASCII TAB rendering from synthetic or provided note events.
- Unit tests for schemas, candidate generation, CLI behavior, and rendering.

### Acceptance Criteria

- The package imports successfully.
- The CLI exposes at least a help/version path and one safe development command.
- Standard-tuning candidate generation is deterministic and tested.
- ASCII TAB output can be produced from a small synthetic fixture.
- `uv run pytest` passes without network access, GPU access, or real audio/video files.
- No 7-string guitar, bass guitar, or custom tuning support is claimed.

### Risks

- Package naming or schema choices may become hard to change later.
- The audio-only baseline may be mistaken for a complete transcription system.
- Too many dependencies may be added before module boundaries are stable.

### What Should Not Be Done Yet

- Do not implement full video processing.
- Do not implement 7-string guitar, bass guitar, or custom tuning support.
- Do not add a web UI.
- Do not add custom model training.
- Do not claim support for YouTube or arbitrary videos.
- Do not commit large media fixtures.

## Phase 1: Manual Fretboard Calibration, Frame Extraction, Left-Hand Evidence

### Goal

Add the first useful video signal: a manually calibrated fretboard and time-aligned left-hand evidence that can later guide string/fret selection.

Phase 1 remains limited to six-string standard-tuning guitar. Video calibration and coordinate work should avoid unnecessary hard-coding where a small abstraction is easy, but it should not implement multi-instrument or custom-tuning behavior.

### Deliverables

- Frame extraction command or adapter.
- Manual fretboard calibration schema and JSON format.
- Calibration load/save support.
- Coordinate system documentation and tests.
- Synthetic or mocked hand landmark input.
- Initial mapping from landmarks to fret/string likelihood regions.
- Debug output showing visual evidence over time.

### Acceptance Criteria

- A user or test fixture can provide calibration for a frame.
- Calibration can be serialized and loaded.
- Coordinate mapping is deterministic and unit-tested with synthetic points.
- Left-hand evidence can be aligned to note timestamps.
- Missing calibration produces a clear error.

### Risks

- Coordinate conventions may become ambiguous.
- Manual calibration may be too awkward without UI support.
- Hand landmarks may be noisy, occluded, or unavailable.
- Video evidence may be overtrusted before it is validated.

### What Should Not Be Done Yet

- Do not require fully automatic fretboard detection.
- Do not require real-time video processing.
- Do not rely on large real video fixtures in unit tests.
- Do not implement right-hand inference yet.
- Do not support arbitrary camera motion.
- Do not implement 7-string guitar, bass guitar, or custom tuning support yet.

## Phase 2: Fusion Decoder, Synchronized Review Output, Better Confidence

### Goal

Combine audio note events, string/fret candidates, left-hand evidence, and playability constraints into a coherent TAB event sequence with inspectable confidence.

### Deliverables

- Candidate scoring model with pitch constraint, left-hand likelihood, playability prior, and transition cost.
- Simple deterministic decoder for initial use.
- Optional Viterbi or beam search prototype once scoring is stable.
- Synchronized review JSON containing notes, candidates, selected positions, scores, warnings, and `needs_review` markers.
- Confidence calculation and calibration buckets.
- Regression tests for mapping, scoring, and decoding.

### Acceptance Criteria

- The decoder selects a deterministic TAB sequence for a synthetic test case.
- Score breakdowns are visible in JSON.
- Low-confidence or conflicting evidence is marked for review.
- String/fret accuracy can be measured against small annotations.
- Existing audio-only behavior remains testable.

### Risks

- Hand-authored costs may overfit a few examples.
- Multiple valid fingerings may make strict accuracy misleading.
- Confidence may appear more precise than it really is.
- Decoder complexity may grow faster than test coverage.

### What Should Not Be Done Yet

- Do not optimize for publication-quality notation.
- Do not implement broad technique support.
- Do not train a model to replace the decoder.
- Do not hide score details behind opaque decisions.
- Do not treat alternate valid fingerings as always wrong.

## Phase 3: Source Separation, Right-Hand Evidence, Export Formats

### Goal

Improve robustness for guitar-forward recordings and add richer output options after the core fusion path is working.

### Deliverables

- Optional source separation adapter, likely Demucs, behind a dependency boundary.
- Evaluation comparing audio note extraction with and without separation.
- Right-hand string likelihood prototype.
- Integration of right-hand likelihood into fusion scoring.
- Export adapters for MusicXML and/or GuitarPro-compatible formats, after JSON and ASCII TAB are stable.
- Design and implement `InstrumentProfile` support only if the six-string pipeline is stable enough to preserve existing behavior.
- Graceful skip behavior for optional heavy dependencies.

### Acceptance Criteria

- Source separation is optional and documented.
- Right-hand evidence can influence string choice in controlled tests.
- Exported files are generated from the same internal `DecodedTabEvent` representation.
- Existing JSON and ASCII TAB outputs remain stable.
- Any 7-string guitar, bass guitar, or custom tuning support is profile-driven and covered by regression tests.
- Tests pass when optional dependencies are unavailable.

### Risks

- Source separation may introduce artifacts that hurt transcription.
- Right-hand tracking may be unreliable in common camera angles.
- Export format work may distract from core transcription quality.
- Heavy dependencies may make installation fragile.

### What Should Not Be Done Yet

- Do not make source separation mandatory.
- Do not support dense multi-guitar separation as an MVP promise.
- Do not add export formats before the internal schema is stable.
- Do not prioritize notation polish over editable TAB usefulness.
- Do not add ad hoc 7-string, bass, or custom tuning branches without a small profile abstraction.

## Phase 4: Web UI, Correction Workflow, Dataset Collection

### Goal

Turn the pipeline into a usable correction workflow and collect better evaluation data from real user edits.

### Deliverables

- Web UI for upload or local file selection.
- Interactive manual fretboard calibration.
- TAB preview synchronized with video/audio time.
- Editing workflow for correcting string/fret choices and notes.
- Export of corrected annotations.
- Dataset collection format and consent/licensing guidelines.
- Metrics for human correction time and edit operations.

### Acceptance Criteria

- A user can calibrate, generate, review, correct, and export a TAB draft.
- Corrections can be saved as structured annotations.
- Review UI highlights low-confidence events.
- Collected examples can be reused for regression evaluation.
- CLI and core modules remain reusable outside the UI.

### Risks

- UI work may force premature changes to core schemas.
- Annotation collection may create privacy or licensing concerns.
- Correction UX may become too complex for the target user.
- Web-specific assumptions may leak into core modules.

### What Should Not Be Done Yet

- Do not replace the CLI with the web UI.
- Do not collect copyrighted third-party videos without a clear policy.
- Do not build social/sharing features.
- Do not optimize for mobile UI before the workflow is proven.

## Phase 5: Optional Custom Model Training

### Goal

Consider custom models only after modular OSS-based approaches have clear, measured limitations and enough annotated data exists to justify training.

### Deliverables

- Written design note identifying the limitation that training should solve.
- Dataset quality report and annotation coverage.
- Baseline comparison against existing OSS/model-based pipeline.
- Training experiment plan with evaluation metrics.
- Small, isolated prototype if justified.
- Rollback path if the custom model does not outperform simpler methods.

### Acceptance Criteria

- A specific failure mode cannot be solved well by simpler modular changes.
- Enough annotated examples exist for meaningful validation.
- The custom model is evaluated against Phase 0-4 baselines.
- Training, inference, and dependency costs are documented.
- The production pipeline can still run without the custom model when appropriate.

### Risks

- Training may consume time without improving the user workflow.
- A custom model may reduce transparency and debuggability.
- Dataset bias may make results worse on real user videos.
- Model maintenance may exceed project capacity.

### What Should Not Be Done Yet

- Do not train custom models speculatively.
- Do not replace transparent scoring without a measured reason.
- Do not make custom model inference mandatory.
- Do not use unlicensed or unclear training data.
- Do not skip evaluation against simpler baselines.
