---
name: Bug report
description: Report a reproducible problem in the current local-first audio-to-TAB MVP
title: "Bug: "
labels: ["type:bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting a bug. Please keep reports focused on the current MVP: short, clean guitar audio, standard 6-string guitar, standard tuning, and local CLI/web workflows.

        Do not upload copyrighted third-party audio or video unless you have the right to share it publicly in this repository.
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What went wrong?
    validations:
      required: true
  - type: dropdown
    id: workflow
    attributes:
      label: Workflow
      options:
        - CLI: audio-to-notes
        - CLI: audio-to-tab
        - CLI: notes-to-tab
        - CLI: candidates
        - Local web UI
        - Documentation
        - Other
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Reproduction steps
      description: Give the smallest command, settings, or UI path that reproduces the issue.
      placeholder: |
        1. Run ...
        2. Upload/select ...
        3. Observe ...
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual behavior
    validations:
      required: true
  - type: textarea
    id: input
    attributes:
      label: Input material
      description: Describe the input without uploading copyrighted third-party material.
      placeholder: "Example: self-recorded 12-second clean single-note phrase, WAV, standard-tuned electric guitar."
    validations:
      required: false
  - type: checkboxes
    id: rights
    attributes:
      label: Media rights check
      options:
        - label: I am not attaching copyrighted third-party audio/video without permission.
          required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
      placeholder: |
        OS:
        Python:
        uv:
        Basic Pitch installed? yes/no
    validations:
      required: false
---
