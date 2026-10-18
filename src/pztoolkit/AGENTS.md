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
  while 42.21 restored it. Keep authenticated predefined god-mode/editor
  operations usable without a compiler. Report Lua availability separately
  from connection readiness; never evaluate operation names or arguments.
- Harness success covers synchronous assertions only. Deferred callback failures
  require a future asynchronous completion protocol. OnTick heartbeat can become
  stale while a world is paused; make that limitation explicit in diagnostics.
- `mod_check` validates the toolkit's `42/` scaffold. Keep broader version-folder,
  dependency, Java, map, asset, and multiplayer validation in the roadmap until
  each capability has its own supported contract and verification.
- Write machine-readable scenario evidence and distinguish game failure, timeout,
  malformed response, and successful assertions.
- Enable god mode once per loaded player through OnCreatePlayer, with a tick
  fallback, only with a token, debug and local single-player guards. Preserve
  later manual disablement. Heartbeats report actual `god_mode` and API errors.
  Before launch, refresh a changed bundled bridge in the owned profile with a
  backup, preserve the token, and enable the bridge. Never refresh a tracked
  running game. Debug remains a launcher argument.
- Keep MCP stdout reserved for protocol traffic.
- `gui.py` is a native Tk adapter that dispatches through `Toolkit.call`. Keep
  tool work on a serialized worker and widgets on the Tk thread. Show errors
  and inconclusive timeouts in the window. Settings default to
  `%LOCALAPPDATA%/PZToolkit/config.json` and existing values are reused.
- Present a direct game toolbelt with connection, god mode and built-in editor
  actions. No mod manager, folder controls, scenario files or authoring workflow.
  Use existing saved settings automatically and keep raw output behind Details.
  `lua_execute` uses fixed authenticated wire files without workspace/report
  creation. Connection requires a fresh `ready=true` heartbeat.
- `GAME_TOOL_NAMES` is the default CLI/MCP/GUI registry view. Keep schemas and
  dispatch shared. Legacy authoring tools need explicit CLI --all-tools.
- `discovery.py` owns bounded read-only detection used internally when no saved
  connection exists and by legacy `folders_detect`. Scan Steam metadata and
  known locations, never whole drives or normal saves as a test profile.

## Work Guidance

Add small slices with tests for observable behavior. Keep adapters thin and use
the installed game's Lua files as the version-specific source of truth.

## Verification

Run the relevant tests under `tests/`. Only a real client run can validate Lua
API assumptions, launch flags, and mod activation for the installed game build.

## Child DOX Index

- `assets/gui/AGENTS.md`: studio artwork, typography, licenses and packaging.
  This parent owns the GUI adapter, shared core, bridge and other package files.
