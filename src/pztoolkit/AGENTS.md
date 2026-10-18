# Purpose

Implement shared Project Zomboid development tools and their adapters.

## Ownership

This subtree owns Python tools, configuration, desktop/CLI/MCP presentation, harness
transport, and packaged Lua bridge assets.

## Local Contracts

- Define tools once in the registry. CLI and MCP expose the same names and input
  contracts and invoke the same implementation.
- Resolve and constrain filesystem paths before writes and source reads.
- Bridge execution is local, opt-in, authenticated, and confined to the isolated
  debug single-player profile; require both client and server networking flags
  to be false. Bound requests, responses, and waits; correlate response IDs.
- Use `.txt` for in-game wire files, including JSON status and response payloads.
  The inspected Build 42.20 file-writer allowlist rejects `.json` filenames.
- Check compiler capability at runtime; 42.20.4 removed dynamic compilation,
  while 42.21 restored it. Report unavailable compilation as a readiness reason.
- Harness success covers synchronous assertions only. Deferred callback failures
  require a future asynchronous completion protocol. OnTick heartbeat can become
  stale while a world is paused; make that limitation explicit in diagnostics.
- `mod_check` validates the toolkit's `42/` scaffold. Keep broader version-folder,
  dependency, Java, map, asset, and multiplayer validation in the roadmap until
  each capability has its own supported contract and verification.
- Write machine-readable scenario evidence and distinguish game failure, timeout,
  malformed response, and successful assertions.
- Keep MCP stdout reserved for protocol traffic.
- `gui.py` is a native Tk adapter that dispatches through `Toolkit.call`. Keep
  tool work on a serialized worker and widgets on the Tk thread. Block actions
  with unsaved setup changes, preserve unsaved scenario edits across workspace
  switches, and show errors and inconclusive timeouts in the window. Settings
  default to `%LOCALAPPDATA%/PZToolkit/config.json`; writes still require Save.
- Present native sidebar pages and a resizable activity dock. The optional
  eight-step guide points to actual controls, permits manual navigation and
  advances automatically only after the matching successful action. Bridge
  readiness requires `ready=true`; only a passing harness result completes it.
  Never execute tools merely by navigating the guide.
- `discovery.py` owns bounded read-only folder detection. Reuse it in GUI,
  shared `folders_detect` tool and configuration-free CLI `detect`. Scan Steam
  library metadata and known locations, not whole drives. Never adopt normal
  Zomboid saves as a test profile. GUI detection previews paths without saving.

## Work Guidance

Add small slices with tests for observable behavior. Keep adapters thin and use
the installed game's Lua files as the version-specific source of truth.

## Verification

Run the relevant tests under `tests/`. Only a real client run can validate Lua
API assumptions, launch flags, and mod activation for the installed game build.

## Child DOX Index

- `assets/gui/AGENTS.md`: studio artwork, typography, licenses and packaging.
  This parent owns the GUI adapter, shared core, bridge and other package files.
