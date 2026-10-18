# Delivery plan

This is the authoritative delivery checklist for the accepted mod development
MVP. It uses this repository's `docs/` convention rather than duplicating tasks
under another directory. See [design](design.md) for contracts and scope.

| Order | Slice | Acceptance | Verification | Depends on |
| --- | --- | --- | --- | --- |
| 1 | Package and shared registry | Registry exposes typed schemas and validates dispatch | Registry success/error tests; package import | None |
| 2 | Read installed Lua sources | Read/search stay in configured root and bound output | Fixture source tree, traversal and limits tests | 1 |
| 3 | Mod authoring | Toolkit 42/ scaffold validates; supported invalid metadata/layout produces findings | Temporary mod fixtures and CLI invocation, JSON argument files | 1 |
| 4 | CLI and MCP adapters | Tool lists and invocation use the shared registry | CLI subprocess checks, actual SDK stdio handshake | 1 |
| 5 | Isolated deploy and launch | Copies and launcher args stay within toolkit profile | Temporary profile tests and launcher command inspection | 3 |
| 6 | Bridge and scenario evidence | Correlated authenticated request, bounded wait, synchronous JSON result over .txt wire files | Offline response/error tests, compiler capability and single-player checks, inspect Lua syntax | 5 |
| 7 | Live game acceptance | Bridge activates and game returns passing/failing assertions | Real debug single-player session with retained evidence | 6 |
| 8 | Release preparation | README commands work, DOX indexes current, repo published | Full tests, package build, link check, GitHub remote inspection | 2-6 |

Parent and source adapters can develop in parallel after registry contracts are
settled. The bridge and harness share a wire contract and need coordinated edits.
Documentation and DOX may proceed independently of executable implementation.

## Checkpoints

- [x] Shared tool discovery and validation work through both adapters.
- [x] Source, scaffold, validation, deployment, and profile checks pass offline.
- [x] Harness distinguishes success, assertion failure, malformed response, and
  timeout; JSON evidence survives each terminal outcome. A pass covers synchronous
  assertions only, and `.txt` filenames satisfy the game's writer restrictions.
- [x] Compiler-unavailable builds and paused/stale heartbeats produce useful
  readiness diagnostics; both multiplayer client and server contexts are refused.
- [ ] Real game acceptance passes with a recorded game version.
- [x] README, package install, relevant tests, and publishing checks pass.
- [x] Native desktop workflow uses the shared registry for mod management and
  scenario runs, with serialized background work and explicit configuration saves.

Keep unchecked game acceptance visible when the executable cannot be launched or
the bridge cannot be exercised. Publishing an initial repository does not imply
the live-game checkpoint passed.

## Desktop redesign acceptance

- [x] Charcoal, ivory and studio-red sidebar layout preserves the approved logo.
- [x] Optional eight-step guide points to controls and supports manual navigation.
- [x] Guide regression tests distinguish successful actions from failures and
  unavailable bridge readiness.
- [ ] All three pages, guide arrows, focus and error states pass native rendered
  checks at default and minimum window sizes.
- [ ] Frozen v0.3.0 GUI, CLI and MCP pass executable checks and release CI.

These checkpoints do not establish live in-world assertions.

## Verification method

Run focused tests as each executable slice lands, then the full pytest suite.
Smoke-test installed CLI commands and MCP stdio. Build a wheel and inspect that
Lua bridge assets are included. Use temporary directories and mocked processes
for offline tests, then test real launch/activation separately. Review correctness,
path containment, token handling, timeout semantics, and adapter parity before
commit. Record actual commands/results in the release handoff, not guessed
counts in this plan.

## Risks and response

| Risk | Response |
| --- | --- |
| Installed build differs from target | Read installed Lua, record version, retain compatibility gap |
| Mod activation differs by version | Verify activation in live client before claiming acceptance |
| Lua scenario stalls game | Use trusted terminating snippets and disposable profile/save |
| Compiler disabled by hotfix | Check runtime capability; explain unsupported compilation before submission |
| World paused | Explain stale OnTick heartbeat and resume requirement |
| Deferred assertion executes after success | Restrict MVP to synchronous scenarios; add explicit future completion protocol |
| Console log cleared at size cap | Preserve JSON reports; disclose potentially incomplete log excerpts |
| Timeout after code already ran | Return unknown outcome; inspect evidence before any retry |
| Environment cannot launch game | Complete offline checks and publish explicit live-test limitation |

## Later capability checkpoints

Keep dependency/version-folder semantics, Java mods, maps/assets, multiplayer
testing, and ZBSpec integration outside the current scaffold validator's claim.
Plan each extension with its own build applicability and acceptance fixtures.
Async scenarios need a tick-driven completion state machine before callback
assertions can contribute to a scenario verdict. The four requested research
passes and unresolved source gaps are recorded in `research.md`.
