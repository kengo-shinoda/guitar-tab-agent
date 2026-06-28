---
name: Feature request
description: Suggest a scoped improvement or future feature
title: "Feature: "
labels: ["type:feature"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for suggesting a feature. The current MVP is intentionally narrow: short, clean guitar audio; standard 6-string guitar; standard tuning; monophonic or mostly single-note phrases; local CLI/web workflows.

        Please distinguish current-MVP improvements from future work such as dense polyphony, full-song transcription, arbitrary video ingestion, custom tunings, or hosted service features.
  - type: textarea
    id: problem
    attributes:
      label: Problem or user need
      description: What user problem would this solve?
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Proposed feature
      description: Describe the smallest useful version of the feature.
    validations:
      required: true
  - type: dropdown
    id: scope
    attributes:
      label: Scope fit
      options:
        - Current audio-only MVP
        - Near-term human-in-the-loop workflow
        - Future video/left-hand evidence
        - Future export/notation support
        - Future hosted/mobile/commercial layer
        - Unsure
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Any simpler workaround or smaller version?
    validations:
      required: false
  - type: checkboxes
    id: non_goals
    attributes:
      label: Scope check
      options:
        - label: This request does not assume exact ground-truth fingering from audio alone.
          required: true
        - label: This request does not require copyrighted third-party demo material.
          required: true
---
