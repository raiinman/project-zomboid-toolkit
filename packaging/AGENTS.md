# Purpose

Build reviewable Windows application bundles and record security gates.

## Ownership

Frozen entry points, clean build adapter, dependency-origin checks, optional
trusted signing, Defender scan gate and frozen application smoke checks.

## Local Contracts

- Distribute complete separate `PZToolkit/` and `pz/` one-folder bundles with
  their support files. Keep native EXE entry points and no user Python requirement.
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

## Work Guidance

Use clean Windows CI for candidate builds. Do not rebuild until a detection goes
away or interpret packaging/signing changes as antivirus clearance.

## Verification

`tests/test_packaging.py` checks origin gates, receipt failures and distribution
contracts without executing application binaries. Frozen probes run only after
the scan gate succeeds in CI; native game acceptance is separate.

## Child DOX Index

No children.
