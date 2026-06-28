# Local web UI upload handling review

This document records the public-alpha review of upload handling in the local web
UI.

The current local web UI is a development/demo interface for trusted local use.
It is not a production hosted service and should not be exposed directly to the
public internet.

## Current behavior

As of this review:

- The default host is `127.0.0.1`.
- The default port is `8765`.
- The upload endpoint is `POST /generate`.
- The upload size limit is `50 MiB`.
- Uploaded bytes are read from the request body.
- The client sends the original browser filename in the `X-Filename` header.
- Only the suffix of the provided filename is used.
- Uploaded bytes are written to a file named `upload<suffix>` inside a
  `TemporaryDirectory`.
- The temporary directory is removed after the transcription workflow returns or
  raises.
- The local web UI does not provide authentication, persistence, accounts, or
  multi-user isolation.

## Path handling

The local server does not write uploaded files to a path derived directly from
the user-provided filename. It extracts only the suffix with `Path(filename).suffix`
and writes to `upload<suffix>` inside a fresh temporary directory.

This avoids a direct filename-based path traversal issue in the current upload
path.

## File type handling

The browser form uses `accept="audio/*"`, but this is only a client-side hint. The
server currently does not enforce a strict audio MIME type or extension allowlist.

For local trusted use this is acceptable for the current public alpha, but a
hosted or multi-user deployment should add server-side validation and clearer
error reporting.

## Size limits

The server rejects uploads larger than `MAX_UPLOAD_BYTES`, currently `50 MiB`.
This is useful for local use but should not be treated as sufficient abuse
prevention for a public service.

A hosted deployment would need stricter limits, rate limiting, request timeout
handling, and monitoring.

## Temporary files

The current upload path uses `tempfile.TemporaryDirectory`, so uploaded files are
stored briefly and removed when processing finishes.

This supports the local-first privacy story, but users should still avoid
processing private or third-party material they do not have the right to use.

## Public deployment warning

Do not expose `tabgen web` directly to the public internet.

A production web service would need at least:

- authentication and authorization
- server-side file type validation
- stricter upload limits
- request timeout handling
- rate limiting
- storage and deletion policy
- logging and monitoring policy
- privacy policy and terms for user-submitted audio
- dependency and model asset review
- security review for path handling and temporary files

## Follow-up items

Potential future hardening tasks:

- Add tests for oversized uploads.
- Add tests that unusual filenames cannot affect output paths.
- Consider a small server-side extension allowlist for `.wav`, `.mp3`, `.m4a`,
  `.flac`, and `.ogg` for clearer user feedback.
- Document whether generated intermediate `NoteEvent` data is retained or only
  returned to the browser.
- Add an explicit local-only warning to the web UI page.
