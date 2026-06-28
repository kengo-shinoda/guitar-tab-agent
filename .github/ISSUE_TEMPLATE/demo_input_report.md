---
name: Demo or input example report
description: Share a safe, minimal example that demonstrates behavior
title: "Example: "
labels: ["type:example"]
body:
  - type: markdown
    attributes:
      value: |
        Use this template for safe, minimal examples that help evaluate the current MVP.

        Please do not attach copyrighted songs, arbitrary YouTube clips, streaming-service audio, or third-party videos unless you have explicit redistribution rights.
  - type: textarea
    id: summary
    attributes:
      label: What does this example demonstrate?
      placeholder: "Example: Candidate 2 is more natural than Candidate 1 for a 5th-position phrase."
    validations:
      required: true
  - type: dropdown
    id: material_type
    attributes:
      label: Material type
      options:
        - Synthetic note JSON
        - Self-recorded audio
        - Public-domain audio
        - Properly licensed audio
        - Description only, no media attached
    validations:
      required: true
  - type: textarea
    id: rights
    attributes:
      label: Rights or license information
      description: Explain why this material can be shared publicly here, or state that no media is attached.
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Reproduction steps
      description: Commands, settings, or UI steps.
      placeholder: |
        uv run tabgen audio-to-tab input.wav --out tab.txt --min-confidence 0.55
    validations:
      required: false
  - type: textarea
    id: observed
    attributes:
      label: Observed output or behavior
    validations:
      required: false
  - type: textarea
    id: desired
    attributes:
      label: Desired output or behavior
      description: What would a better candidate or correction look like?
    validations:
      required: false
---
