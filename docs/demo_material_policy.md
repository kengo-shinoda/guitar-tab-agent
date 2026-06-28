# Demo material policy

This policy defines which audio, video, and example inputs are safe to include in
`guitar-tab-agent` issues, tests, docs, examples, and public demos.

The project is intended to help users create editable guitar TAB drafts from
material they have the right to process. It should not encourage copying,
downloading, converting, or redistributing third-party copyrighted media.

## Allowed material

The following material is acceptable for repository fixtures, examples, and
public demos when the origin is clear:

- synthetic note data generated for tests
- synthetic audio generated for tests
- short self-recorded guitar audio created specifically for this project
- public-domain material
- Creative Commons or other openly licensed material that permits redistribution
- small metadata-only examples that do not include the original media
- screenshots or short clips of the local UI that do not include copyrighted
  songs or private user material

When using openly licensed material, include enough attribution and license
information to verify that redistribution is allowed.

## Material to avoid

Do not commit, upload, or redistribute the following in this repository:

- commercial songs
- arbitrary YouTube, TikTok, Instagram, X/Twitter, or streaming-service audio
  or video
- third-party guitar covers with unclear rights
- lesson videos or backing tracks that are not explicitly redistributable
- private user recordings without explicit permission
- unreleased or confidential recordings
- large binary media files without a clear need and license

If an example requires such material to reproduce locally, describe the steps
without committing the file.

## Issue reports

Issue reports should describe the input material in words when possible. For
example:

```text
Self-recorded 12-second clean electric guitar phrase, standard tuning, mostly
single-note melody around the 5th position.
```

If attaching audio or video, the reporter should confirm that they have the
right to share it publicly in the repository.

## Tests

Prefer tests that use:

- small synthetic `NoteEvent` JSON fixtures
- generated tones
- mocked transcription workflows
- short self-created fixtures with explicit repository permission

Tests should not require downloading media from YouTube or any streaming
service.

## Documentation and demos

Documentation should avoid implying support for arbitrary songs, full mixes, or
web-video ingestion. Public demos should use owned, generated, public-domain, or
properly licensed material.

## Maintainer checklist

Before accepting a PR that adds media or demo material, check:

- Is the material necessary?
- Is the source and license clear?
- Does the license permit redistribution in this repository?
- Is attribution included when required?
- Could a synthetic or text-only example work instead?
- Does the example keep the product framed as local-first, candidate-based TAB
  draft generation rather than exact automatic transcription?
