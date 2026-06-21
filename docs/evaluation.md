# Evaluation

## Goal

Evaluate whether the app produces an editable guitar TAB draft that reduces manual transcription effort. The MVP should be tested with small, manually annotated examples before attempting broad real-world coverage.

## MVP Evaluation Set

Use short fixed-camera clips that match MVP assumptions:

- six-string guitar,
- standard tuning,
- visible fretboard,
- solo guitar or guitar-forward audio,
- simple fretted notes before advanced techniques,
- manual reference annotations created by a guitarist or reviewer.

The first evaluation set can be very small: a few clips of 5 to 20 seconds each. Quality of annotation matters more than dataset size at this stage.

## Suggested Annotation Format

Reference annotations can be stored as CSV or JSON rows with these fields:

- `video_id`: stable clip identifier.
- `start_time`: note start time in seconds.
- `end_time`: note end time in seconds.
- `pitch_midi`: expected MIDI pitch.
- `string`: expected guitar string, where 1 is high E and 6 is low E.
- `fret`: expected fret number, where 0 is open string.
- `technique`: plain, bend, slide, hammer_on, pull_off, harmonic, muted, unknown, or other controlled label.
- `confidence/comment`: annotator confidence and optional free-text note.

Example:

```csv
video_id,start_time,end_time,pitch_midi,string,fret,technique,confidence/comment
clip_001,1.250,1.520,64,1,0,plain,high
clip_001,1.540,1.820,67,1,3,plain,medium; slight timing uncertainty
```

## Audio Note Detection Metrics

Measure whether the audio stage finds note events before string/fret assignment.

- Precision: generated note events that match a reference note.
- Recall: reference notes that are detected.
- F1 score: harmonic mean of precision and recall.
- False positives per second: extra detected notes that would burden correction.
- Missed notes per clip: reference notes with no matching detection.

For MVP, matching should use a practical onset tolerance and pitch match rather than strict symbolic notation alignment.

## Pitch Accuracy

Pitch accuracy measures whether matched generated notes have the correct MIDI pitch.

- Exact pitch accuracy: percentage of matched notes with identical `pitch_midi`.
- Semitone error distribution: counts of errors by interval, such as -12, -1, +1, +12.
- Octave error rate: percentage of pitch errors that are octave mistakes.

Pitch accuracy should be reported separately from string/fret accuracy because the same pitch can be played in multiple positions.

## Onset Timing Tolerance

Onset matching should use tolerances appropriate for an editable TAB draft.

Suggested initial tolerances:

- strict: within 50 ms,
- practical MVP: within 100 ms,
- loose diagnostic: within 200 ms.

Report onset mean absolute error and median absolute error for matched notes. Duration accuracy can be tracked later, but onset quality is more important for early TAB usefulness.

## String/Fret Accuracy

String/fret accuracy measures whether the fusion stage selects the same playable position as the reference.

- String accuracy: selected string matches the reference string.
- Fret accuracy: selected fret matches the reference fret.
- Exact position accuracy: both string and fret match.
- Playable pitch accuracy: selected string/fret produces the correct pitch even if it differs from the reference fingering.
- Ambiguous-position rate: percentage of notes where multiple positions are musically plausible.

MVP reports should distinguish wrong pitch from alternate valid fingering. A different fingering may still be useful if the resulting TAB is playable and easy to correct.

## Edit Distance Against Reference TAB

Compare generated TAB to reference TAB using a simple event-level representation rather than visual ASCII spacing alone.

Suggested sequence item:

```text
(rounded_start_time, string, fret, technique)
```

Metrics:

- insertion count: extra generated events,
- deletion count: missed reference events,
- substitution count: wrong string/fret/technique for matched events,
- normalized edit distance: total edits divided by reference event count.

ASCII TAB can also have a golden-file comparison for small tests, but event-level edit distance should drive evaluation.

## Human Correction Time

The most important product metric is whether the generated draft saves time.

Measure:

- time to create TAB from scratch,
- time to correct generated TAB,
- number of manual edits made,
- subjective usefulness rating from the reviewer,
- notes about frustrating failure modes.

For MVP, a generated draft is successful if an amateur or intermediate guitarist can correct it faster than starting from an empty TAB for simple clips.

## Confidence Calibration

The system should expose confidence and `needs_review` markers that are meaningful.

Track:

- accuracy by confidence bucket, such as 0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0,
- whether low-confidence events are actually more likely to be wrong,
- false confidence: high-confidence wrong events,
- overflagging: correct events marked as needing review.

Confidence does not need to be perfect early, but it should help users decide where to inspect first.

## Failure Mode Categories

Classify errors so future work can target the right module.

- Audio miss: a reference note was not detected.
- Audio false positive: an extra note was generated.
- Pitch error: note detected with wrong MIDI pitch.
- Onset error: note detected too early or too late.
- Duration/grouping error: note length or grouping is misleading.
- Candidate mapping error: pitch-to-string/fret candidates are wrong.
- Fusion error: correct candidate exists but the wrong position was selected.
- Left-hand evidence error: calibration or landmarks point to the wrong fret/string.
- Right-hand evidence error: picking string likelihood is wrong or unavailable.
- Playability prior error: movement or fingering cost biases the decoder incorrectly.
- Technique unsupported: bend, slide, harmonic, muted note, or other technique is outside MVP capability.
- Annotation ambiguity: reference is uncertain or multiple fingerings are valid.
- Input unsupported: video/audio violates MVP assumptions.

## Do Not Optimize Too Early

The first target is a useful editable draft, not perfect transcription. Early evaluation should reward transparency, predictable behavior, and reduced correction time over leaderboard-style accuracy.

Do not overfit the system to a tiny benchmark by adding complex heuristics too soon. Prefer simple metrics, clear failure labels, and small regression tests that explain what improved or broke. Once the basic pipeline reliably produces editable drafts for controlled clips, broader accuracy optimization can begin.
