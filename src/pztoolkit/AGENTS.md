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
- Open on Offline tools, with saved test-profile logs, literal installed-script
  search, bounded source excerpts and read-only settings checks available without
  a live connection. Missing logs are a normal empty state. First offline use may
  detect and save app-owned settings, but must not prepare a profile, install a
  bridge or launch the game. Keep readable results on the page, raw JSON in Details.
- Missing or unowned profile log/status reads return a normal empty/not-ready
  result without creating files or reading unowned content. Report game_state as
  world_loaded for fresh readiness, running/closed only after inspecting a tracked
  process, and unknown when no process evidence exists.
- Live god-mode/editor/Lua buttons require a successful fresh readiness check;
  recheck in the serialized worker before dispatch, since a world may close or
  pause after a previous check. Explain loaded debug single-player/unpaused
  requirements and preserve offline access when live commands fail. Only call
  the game closed when the core reports proof of an exited tracked process.
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

GUI smoke reports exercise offline settings only, check bundled bridge assets,
record the initial page and detect unwanted profile creation. Mapped layout
verification runs in CI; local maintenance keeps test windows withdrawn.
Run the relevant tests under `tests/`. Only a real client run can validate Lua
API assumptions, launch flags, and mod activation for the installed game build.

## Child DOX Index

- `assets/gui/AGENTS.md`: studio artwork, typography, licenses and packaging.
  This parent owns the GUI adapter, shared core, bridge and other package files.
