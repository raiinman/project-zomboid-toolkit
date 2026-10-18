# Project Zomboid toolbelt architecture

## Objective and scope

Connect the desktop app, CLI and Codex/MCP to a running debug single-player game.
The user edits an existing mod; toolkit use must not require mod creation, a
folder wizard, a new workspace or saved scenario files. The game and Steam retain
mod-management authority. This is a game/debug/editor toolbelt, without a claim
of UEFN Toolbelt feature parity.

Build 42 on Windows is the initial target. Installed build evidence determines
compatibility. The four research passes are in [research](research.md); a hotfix
can change compiler capability even within Build 42.

## Shared registry and adapters

One Python registry owns names, descriptions, schemas, validation and dispatch.
`GAME_TOOL_NAMES` selects the 11 normal public tools used by CLI, MCP and GUI:
`doctor`, `bridge_install`, `game_launch`, `bridge_status`, `logs_read`,
`source_search`, `source_read`, `lua_execute`, `god_mode`, `debug_editors`,
`editor_open`.

The complete 17-tool registry retains older file/scaffold operations for existing
scripts, explicitly selected with CLI `--all-tools`. Their presence is backwards
compatibility, not the product's main workflow. Neither mod authoring nor a
scenario file is a dependency of the game connection.

The desktop uses native Windows Tk. CLI uses JSON and exit statuses. MCP uses the
official Python SDK 1.x (`>=1.12.4,<2`) over stdio, reserving stdout for protocol
messages. Both executables bundle Python and bridge assets. CLI and app default
to the saved `%LOCALAPPDATA%/PZToolkit/config.json` connection; `--config` remains
available to existing integrations. Keep current configuration rather than
migrating it into a new project.

## Connection and game authority

`bridge_install` installs or refreshes the small Lua helper using the existing
profile settings. Changed owned helper files receive backups and the token is
preserved. `game_launch` uses the installed game, debug and the existing isolated
cache/profile. Normal saves, unrelated mods and installed game content remain
outside write scope. The separate profile is a safety boundary, not a required
user-created project. The UI exposes no folder or mod manager.

The user enables PZ Toolkit Bridge and their existing mod in the game's Mods
menu, loads a single-player world and unpauses. Launch success alone is not a
connection. `bridge_status` requires a fresh loaded-world heartbeat and reports
actual god mode and readiness failures with a useful next step.

God mode is enabled once for every loaded or respawned player after token and
single-player/debug checks pass. `OnCreatePlayer` handles startup; `OnTick`
covers loading after that event. Heartbeats report actual state and API failures.
Manual disablement remains possible for damage tests rather than being undone
every tick. Before launch, changed helper Lua is refreshed with a backup; tracked
running games prevent unsafe refresh.

## Direct commands and built-in editors

`lua_execute` accepts bounded inline Lua and a wait timeout. It shares the
existing authenticated transport but does not require a workspace/scenario file
or persist a report for each command. Fixed profile wire files carry requests,
status and responses. `god_mode` uses that transport to set and verify state.

`debug_editors` lists allowlisted IDs: `debug`, `vehicle`, `attachment`,
`animation`, `world_map`. `editor_open` requests the corresponding built-in UI
using signatures inspected in shipped `ISDebugMenu` source. Availability depends
on the actual runtime. Successful execution proves the request completed, not
that its window is visible; native inspection is separate evidence.

## Trust and execution contracts

Game source reads/searches stay bounded and read-only within the installation.
Paths are confined to their declared roots; linked paths and traversal are
rejected. Validate inputs before side effects. MCP and CLI preserve the same
machine-readable results and errors. Do not retry mutating game calls blindly:
a missing response does not establish that execution did not occur.

The Lua bridge uses `pzt-request.txt`, `pzt-status.txt` and `pzt-response.txt` for
JSON payloads because the inspected Build 42.20 writer permits `.txt` and rejects
`.json`. Requests carry a token, unique ID, expiry and code. The client validates
the envelope and correlates bounded synchronous responses. Local tokens grant
game-level code execution, not a Lua sandbox.

Only a loaded debug single-player session is accepted, with both `isClient()`
and `isServer()` false. Readiness includes compiler capability: `loadstring` was
disabled in 42.20.4 and restored in 42.21. API documentation alone does not prove
a function is enabled in a particular hotfix. OnTick heartbeat/execution can
stall while paused. Lua must terminate; the host timeout cannot interrupt code
already running and reports an unknown outcome.

Only synchronous assertions count. Registering callbacks does not correlate
their later results with the completed request. Legacy `harness_run` retains its
saved-scenario/report contract behind the explicit full registry; direct commands
do not inherit that file workflow. Logs may truncate or reset, so excerpts can be
incomplete and must not be described as a complete execution history.

## Desktop contract

Connect first, then use game tools. Explain the helper, real game launch,
in-game activation and loaded-world check in plain language. Keep one useful
next action prominent. Existing settings load automatically. No mod creation,
folder selection, deployment tour or scenario saving is required. Technical
output and inline Lua are disclosed deliberately; trust remains explicit.

All actions use `Toolkit.call` on one worker at a time, with UI-thread queue
results. Errors, not-ready states and timeouts have plain distinct messages.
Closing during an action cannot cancel game Lua. The approved distressed logo
is retained byte-for-byte; original decrepit workshop imagery, readable native
controls and no-green styling follow [the visual system](../DESIGN.md).

## Delivery and acceptance

`packaging/build.ps1` builds windowed `PZToolkit.exe`, console `pz.exe` and their
ZIP. A versioned output directory preserves an older running executable.
Frozen entry points reset the Windows DLL directory before launching the game.
Executable checks cover the actual mapped GUI, bundled helper and real MCP
handshake. Source tests cover shared schemas, isolation and protocol behavior.

A release must keep offline tests, executable checks, rendered GUI review and
live game acceptance distinct. Live acceptance needs a recorded game version,
bridge activation, startup god mode, direct passing/failing Lua and visible
built-in editor inspection. Neither mocks nor a successful editor request can
replace that evidence. See [plan](plan.md) and [validation](validation.md).

## Later capabilities

Add further bounded game state/actions and editor operations through the shared
registry. Multiplayer/server administration needs its own trust model. Deferred
assertions need explicit correlated completion before counting as passed.
Legacy mod validation still checks only the toolkit's `42/` structure, not full
asset/dependency/Java/map or multiplayer compatibility. Never broaden that claim
without separate acceptance fixtures.

## Build 42.20.4 compatibility

Connection readiness depends on local authenticated debug single-player state,
not dynamic compilation. Predefined `PZT-OP/1` god-mode/editor commands use the
existing bounded, authenticated, expiring, correlated transport. Names, frame
length and values are strict allowlists, never executable source. Startup god
mode also needs no compiler. `lua_execute` remains available only when the game
provides its compiler; the GUI explains this separate capability.

The official [42.20.4 hotfix notes](https://theindiestone.com/forums/topic/100509-42204-stable-42192-unstable-417821-legacy-hotfixes-released/)
removed loadstring/loadstream and recommended predefined command methods.
[42.21 release notes](https://projectzomboid.com/blog/news/2026/09/42-21-stable-released/)
record later restoration. Runtime capability checks remain authoritative.
