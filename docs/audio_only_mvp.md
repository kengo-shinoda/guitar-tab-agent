# Audio-Only Web MVP

## Product Framing

The short-term product direction is an audio-only guitar TAB draft generator.
The user provides clean, short guitar audio and receives a playable, editable
TAB draft plus intermediate JSON that can be inspected or reused.

The product promise is not perfect ground-truth transcription. The MVP should
reduce manual transcription effort by producing a useful first draft from clean
guitar audio.

Video-assisted disambiguation remains valuable, but it is advanced/future work.
Real-image and video support introduces substantial computer-vision complexity:
hand tracking, fretboard tracing, visible fret ranges, fret-line calibration,
perspective effects, and model asset handling. Those capabilities should stay in
the repository, but they should not define the public MVP path.

## MVP Target

- Standard 6-string guitar.
- Standard tuning.
- Monophonic or mostly single-note phrases.
- Short clips, roughly 10-30 seconds.
- Clean, guitar-forward audio.
- Local-first backend and CLI workflows that can be reused by a future web app.

Primary outputs:

- Playable/editable ASCII TAB draft.
- Intermediate `NoteEvent` JSON for debugging and iteration.

## Public MVP Non-Goals

- Chords and dense polyphony.
- Distorted, noisy, or full-mix audio.
- Exact notation for bends, slides, vibrato, hammer-ons, and pull-offs.
- Source separation.
- Video-assisted disambiguation.
- Fretboard or fret-line tracing.
- Full notation editor.
- MusicXML or GuitarPro export as the first public surface.

## Core Technical Path

The public MVP path should stay small and understandable:

```text
audio -> Basic Pitch note candidates -> filtering -> string/fret candidates
      -> ergonomic decoder -> ASCII TAB
```

Audio provides pitch and timing candidates. The decoder should treat
string/fret ambiguity as an optimization problem, not as a claim that the exact
observed fingering is known. When multiple positions can play the same note, the
MVP should prefer a natural, playable fingering path.

The current decoder direction is sequence-level ergonomic path optimization:
choose the lowest-cost string/fret path across the phrase, not merely the
locally cheapest position for each note. This remains a TAB draft heuristic, not
observed fingering reconstruction.

The decoder also models simple 4-fret position-box continuity. For example, a
phrase that can stay in frets 9-12 across adjacent strings should prefer that
stable hand position when the phrase-level cost supports it. This is still an
ergonomic TAB-draft heuristic, not proof of the player's observed fingering.

## Decoder Direction

The next core product improvements should introduce or strengthen ergonomic path
optimization. A candidate state is the selected string/fret position for each
note. Transition costs should remain transparent and testable.

Candidate cost terms to explore:

- Fret movement.
- String movement.
- Position shifts.
- Repeated-note stability.
- Open-string preference or penalty.
- High-fret penalty.

Later product work can expose tunable weights. Debug score components are
important so users and developers can understand why a path was selected.

## Repository Structure Recommendation

Keep the current monorepo. Do not force a package layout refactor just to
prepare for the web MVP.

Recommended organization:

- `src/guitar_tab_agent/audio/`: audio transcription adapters and note filtering.
- `src/guitar_tab_agent/fusion/`: string/fret candidates and decoder logic.
- `src/guitar_tab_agent/tab/`: ASCII TAB rendering and future export formats.
- `src/guitar_tab_agent/video/`: advanced/future video evidence.
- `src/guitar_tab_agent/web/` or `apps/web/`: future minimal web app.
- `docs/`: product scope, architecture, limitations, roadmap, and future
  multimodal design.
- `examples/`: only safe synthetic or self-generated examples.

The CLI should remain a thin wrapper around reusable workflow functions. A
future local web UI should call the same backend workflows instead of duplicating
audio, decoder, or renderer logic.

## Milestones

Suggested GitHub milestones:

- Milestone 1: Audio-only Web MVP.
- Milestone 2: Editable TAB Draft.
- Milestone 3: Advanced Video Evidence.

Milestone 1 should prioritize the audio path, UX clarity, limitations, safe
examples, and deployable local-first workflows. Milestone 3 should hold
MediaPipe, calibration, fretboard tracing, video evidence, and multimodal fusion
work unless a specific issue explicitly pulls a small video task forward.

## Labels And Categories

Suggested labels:

- `area:audio`
- `area:decoder`
- `area:web`
- `area:cli`
- `area:docs`
- `area:video`
- `area:tests`
- `type:feature`
- `type:bug`
- `type:refactor`
- `type:docs`
- `type:smoke`
- `mvp`
- `future`
- `blocked`

Use `mvp` for work that directly improves the public audio-only product path.
Use `future` for video, multimodal fusion, and broader notation support unless
they are explicitly needed for the current MVP.

## Public-Readiness Checklist

- README frames the product as an audio-only TAB draft generator.
- README explains limitations plainly.
- LICENSE decision is made before broad public launch.
- Optional dependencies are documented clearly.
- Only safe synthetic or self-generated examples are committed.
- No real copyrighted media is committed.
- Generated notes, TAB files, plots, model files, and smoke artifacts are kept
  out of the repository.
- A limitations page or section covers audio quality, monophony assumptions,
  TAB ambiguity, and unsupported techniques.
- The CLI and future web UI share the same backend workflow functions.

## README TODO

Before the public MVP is presented broadly, update the README to:

- Lead with the audio-only product framing.
- Show the shortest audio-to-TAB path.
- Link to limitations and optional Basic Pitch setup.
- Keep video-assisted features clearly labeled as advanced/future work.
