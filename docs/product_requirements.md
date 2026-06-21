# Product Requirements

## 1. Problem

Amateur and intermediate guitarists often want to learn, share, or refine parts from performances, but writing TAB by ear is slow and error-prone. Existing automatic transcription tools can suggest notes, but they usually do not understand guitar-specific constraints such as string choice, fret position, and playable hand movement.

This product should generate an editable TAB draft from a user's own guitar performance video. The goal is to reduce manual transcription effort, not to produce perfect publication-quality notation.

## 2. Target Users

- Amateur and intermediate guitarists.
- Band circle and copy-band players preparing covers.
- Guitarists who record practice or rehearsal videos with a fixed camera.
- Users comfortable correcting a generated TAB draft rather than expecting a final score.

## 3. MVP Scope

The MVP supports:

- local upload of the user's own fixed-camera guitar performance video,
- six-string guitar in standard tuning,
- solo guitar or guitar-forward recordings,
- manual fretboard calibration,
- audio-to-note extraction,
- pitch-to-string/fret candidate generation,
- simple decoding into a playable TAB candidate,
- ASCII TAB output,
- JSON output for future editing and debugging.

## 4. Non-Goals

The MVP explicitly does not support:

- full YouTube or general internet video transcription,
- arbitrary camera angles or poor-visibility videos,
- automatic tuning detection,
- alternate tunings,
- seven-string or extended-range guitars,
- multiple guitar separation,
- dense full-band source separation beyond optional future preprocessing,
- advanced techniques such as bends, slides, vibrato, harmonics, tapping, or palm-muted nuance,
- publication-quality notation,
- MusicXML, GuitarPro, or web UI output,
- automatic custom model training.

## 5. User Workflow

1. The user records or selects a fixed-camera video where the fretboard is visible.
2. The user uploads the local video to the app or runs the CLI against it.
3. The app asks the user to manually calibrate the fretboard if calibration is not already available.
4. The app extracts audio and creates note events.
5. The app generates possible string/fret positions for each pitch.
6. The app combines audio notes, calibration/video evidence, and guitar playability constraints.
7. The app outputs an editable ASCII TAB draft and structured JSON.
8. The user corrects the draft manually.

## 6. Functional Requirements

- Accept a local video file as input.
- Extract audio from the input video.
- Convert audio into note events with onset, duration, pitch, and confidence.
- Store or load manual fretboard calibration data.
- Represent standard tuning explicitly and reject unsupported tunings.
- Generate valid string/fret candidates for each detected pitch.
- Apply guitar-specific constraints such as fret range and movement cost.
- Produce a selected TAB event sequence.
- Render the selected sequence as ASCII TAB.
- Export intermediate and final results as JSON.
- Report unsupported inputs and missing external tools with clear errors.

## 7. Quality Requirements

- Components for audio, video, fusion, and output must remain decoupled.
- Core pitch-to-fret logic must be deterministic and unit-tested.
- Heavy dependencies should be optional or isolated behind adapters.
- The output must be transparent enough for users and developers to inspect why a TAB candidate was chosen.
- Unit tests must avoid large audio/video fixtures and network access.
- The system should fail gracefully when optional tools are unavailable.
- The generated TAB should prioritize editability over overconfident precision.

## 8. Evaluation Criteria

The MVP is successful if:

- standard-tuning pitch-to-string/fret mapping is correct,
- the app can generate ASCII TAB from synthetic or extracted note events,
- the JSON output includes enough information for debugging and future editing,
- a guitarist can correct the generated draft faster than writing TAB from scratch,
- unsupported inputs are clearly rejected,
- unit tests cover candidate generation, decoding basics, and TAB rendering.

Early evaluation should use short, controlled clips and synthetic fixtures before introducing larger media test sets.

## 9. Risks

- Audio transcription may produce wrong pitches or noisy note events.
- Fixed-camera assumptions may fail when hands or fretboard are occluded.
- Manual calibration may be inconvenient without a UI.
- Multiple valid fingerings may make string/fret selection ambiguous.
- Advanced guitar techniques may be misrepresented as plain fretted notes.
- Adding heavy dependencies too early may make installation and testing fragile.
- Overpromising accuracy could make the MVP feel worse than a transparent draft tool.

## 10. Future Phases

- Improve video-based left-hand position likelihood with MediaPipe or similar tools.
- Add optional guitar stem extraction for noisy mixes.
- Add right-hand string evidence.
- Add better rhythm quantization and note grouping.
- Support common guitar techniques after the basic pipeline is stable.
- Add an interactive correction UI.
- Add MusicXML and GuitarPro export.
- Explore alternate tunings and additional guitar types.
- Consider custom model training only after modular OSS-based approaches reach clear limits.
