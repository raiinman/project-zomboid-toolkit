# Purpose

Verify tool contracts and regression behavior independently of game ownership.

## Ownership

Offline unit/integration tests, fixtures, and protocol parity checks.
`test_gui.py` owns real Windows Tk widget flows with temporary workspaces and
simulated bridge responses, including responsive waits and workspace switching.
It also verifies sidebar navigation, guide arrows, successful-action advancement,
completion and failure gating, readable contrast and the no-green control palette.
`test_discovery.py` owns fixture-based Steam/common-folder detection, ambiguity,
read bounds and preservation checks. GUI tests cover first-launch detection,
preview-only settings and visible discovery failures.

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
GUI widget tests run on Windows and are skipped on other CI platforms.

## Child DOX Index

No children currently exist; this file owns all tests and fixtures.
