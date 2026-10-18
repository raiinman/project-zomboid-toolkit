# Purpose

Verify tool contracts and regression behavior independently of game ownership.

## Ownership

Offline unit/integration tests, fixtures, and protocol parity checks.
`test_gui.py` owns native Windows Tk flows for Connection and Game tools,
worker responsiveness, trusted inline Lua, built-in editors, actual status,
readable controls and absence of mod/folder/scenario setup UI.
`test_inline_tools.py` owns inline transport without workspace/report creation,
editor allowlists, strict god-mode booleans and tracked-game install guards.
`test_discovery.py` owns fixture-based Steam/common-folder detection, ambiguity,
read bounds and preservation checks for internal and legacy discovery.
Lua mocks also cover god-mode spawn/respawn/fallback, guarded startup, manual
disablement and API failure reporting. Launch fixtures cover changed bridge
refresh with backup/token preservation and no redeploy of unchanged scripts.

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
