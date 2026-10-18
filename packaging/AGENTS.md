# Purpose

Build reviewable Windows application bundles and record security gates.

## Ownership

Frozen entry points, clean build adapter, dependency-origin checks, optional
trusted signing, Defender scan gate and frozen application smoke checks.

## Local Contracts

- Distribute complete separate `PZToolkit/` and `pz/` one-folder bundles with
  their support files. Keep native EXE entry points and no user Python requirement.
- Register the installed MCP entry point with explicit `--config <saved game
  connection> serve` arguments. Verify this chat's native `doctor` and fresh
  `bridge_status` against the actual PC profile. A standalone stdio probe does
  not establish that an existing chat has reconnected or selected that profile.
- Build with a controlled PATH, locked dependencies, `--onedir --noupx --clean`.
  Reject native inputs outside the active Python, virtual environment and Windows
  system directories, including Codex runtime/libheif origins.
- Signing is optional preparation, never an assertion that an unsigned build is
  signed. Require an unexpired trusted Code Signing certificate with private key,
  SHA-256 signing, RFC3161 timestamp and successful Authenticode verification.
- Before executing a new bundle, complete ordinary Defender scanning with active
  protection, no new detections, unchanged file hashes and an explicit receipt.
  Missing scanner, unknown verdict, changed files or detections fail closed.
- Never restore quarantined binaries, change protection/trust settings, add
  exclusions, upload private files or run a blocked artifact to make a check pass.
- Build/scan receipts contain local paths and belong in ignored `dist/`, not Git
  or the public application ZIP. A passing scan is evidence at one time only.
- Private CI may retain `UNSCANNED-security-staging-<commit>` for two days only
  after a successful clean build and the active/current Defender prerequisite
  fails before any scan. This is scan-only staging, never execution or delivery
  approval. Other failures are ineligible; CI stays failed. Require the same
  exact-bundle and ZIP scan gate on the user's PC before execution or installation.

## Work Guidance

Use clean Windows CI for candidate builds. Do not rebuild until a detection goes
away or interpret packaging/signing changes as antivirus clearance.

## Verification

`tests/test_packaging.py` checks origin gates, receipt failures and distribution
contracts without executing application binaries. Frozen probes run only after
the scan gate succeeds in CI; native game acceptance is separate.

## Child DOX Index

No children.
