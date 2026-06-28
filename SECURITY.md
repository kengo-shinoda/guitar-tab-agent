# Security Policy

## Supported versions

`guitar-tab-agent` is currently an early local-first MVP. Security fixes should
target the default branch unless a release branch is created in the future.

## Local-first security model

The local web UI is intended for personal local use, typically bound to
`127.0.0.1`. It is not designed to be exposed directly to the public internet.

Do not deploy the current local web UI as a public service without adding and
reviewing at least the following:

- authentication and authorization
- upload size and file type limits
- temporary-file cleanup policy
- storage and deletion policy for uploaded audio
- rate limiting and abuse prevention
- path traversal protections
- dependency and model asset review
- privacy policy and terms for user-submitted audio

## User-submitted audio and media

Audio and video files may contain private performances, unreleased material, or
third-party copyrighted content. Contributors and downstream deployers should
avoid storing or redistributing user media unless there is a clear policy and the
necessary rights.

Demo, test, and documentation material should use owned, generated,
public-domain, or properly licensed media.

## Reporting a vulnerability

If you find a security issue, please report it privately if GitHub private
vulnerability reporting is enabled for this repository. Otherwise, contact the
maintainer directly before opening a public issue.

Please include:

- a short description of the issue
- affected command, module, or workflow
- reproduction steps when safe to share
- any relevant environment information

Please do not include private audio, credentials, or sensitive user data in a
public issue.
