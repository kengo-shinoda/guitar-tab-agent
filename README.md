# guitar-tab-agent

Video-assisted guitar tablature transcription app using audio, hand tracking, and guitar-specific fusion decoding.

The Python package is `guitar_tab_agent`. The CLI command is `tabgen`.

## Local Development

Install project and development dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Inspect the CLI:

```bash
uv run tabgen --help
```

## MVP Scope

The MVP focuses on editable TAB drafts for standard-tuned six-string guitar from fixed-camera, guitar-forward videos. JSON and ASCII TAB come first. Full automatic transcription, arbitrary online videos, advanced guitar techniques, and publication-quality notation are later work.
