# Purpose

Verify tool contracts and regression behavior independently of game ownership.

## Ownership

Offline unit/integration tests, fixtures, and protocol parity checks.

## Local Contracts

- Use temporary profiles and fixture game trees for writes.
- Exercise failure behavior, traversal, profile isolation, and CLI/MCP parity.
- Simulated bridge responses verify transport only. Label them as offline
  evidence and keep live game acceptance separate.
- Keep machine-specific game paths and credentials outside fixtures.

## Work Guidance

Prefer observable behavior and small fixtures over implementation mirrors.

## Verification

Use the repository's pytest suite. Report live game tests separately.

## Child DOX Index

No children currently exist; this file owns all tests and fixtures.
