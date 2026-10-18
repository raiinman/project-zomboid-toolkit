# Project Zomboid Toolkit design

## Objective and accepted scope

Give mod developers and AI clients the same tools to inspect installed game
sources, create and validate mods, deploy into an isolated profile, and run Lua
assertions inside a real game. The user authorized implementation, GitHub
repository creation, installation of their DOX framework, relevant skills from
their skill library, and parallel subagents. Routine design decisions below fit
that scope and do not need repeated approval.

The initial compatibility target is Build 42 on Windows. Exact compatibility is
determined by the installed game and captured live evidence. Mod layout and Lua
API assumptions require validation against that build. Dedicated server
administration and character control remain later modules.
The four requested research passes are consolidated in [research](research.md).
Build 42 is not one fixed API: compiler availability and file-writer restrictions
need checks against the actual runtime, even within the same major build.

## Capability map

| ID | Responsibility | Depends on | Initial scope |
| --- | --- | --- | --- |
| shared-tools | Typed tool definitions, discovery, common invocation and errors | None | MVP |
| mod-development | Inspect game Lua, scaffold/validate mods, deploy isolated copies | shared-tools | MVP |
| game-harness | Isolated launch, Lua bridge requests, evidence and log collection | mod-development | MVP |
| cli | Tool discovery and JSON invocation for scripts | shared-tools | MVP |
| mcp | stdio tools for AI clients | shared-tools | MVP |
| server-administration | Server configuration, lifecycle, logs and administration | shared-tools | Roadmap |
| gameplay | Observe game state and execute character actions/scenarios | game-harness | Roadmap |

Build order: shared-tools, then mod-development and adapters, then game-harness.
The architecture stays extensible through additional tool registrations rather
than premature implementations of roadmap modules.

## Accepted decisions

1. **Python core, thin adapters.** One registry owns tool names, descriptions,
   input schemas, and callables. CLI and MCP derive discovery from that registry
   and dispatch through the same call path. This prevents the interfaces from
   drifting. Python 3.11+ supplies the standard-library core. The optional MCP
   Python SDK v1 dependency (`>=1.12.4,<2`) provides stdio protocol handling.
2. **Filesystem bridge first.** A small client Lua mod reads requests and writes
   responses through the game's own file APIs. This avoids native injection and
   a network listener. Local file access is still privileged: bridge tokens,
   profile files, and local processes form a trust boundary.
3. **Isolated profiles.** Toolkit-managed cachedir and mod directories hold
   configuration, generated mods, bridge state, and evidence. Installed game
   sources remain read-only. Normal saves and mods are outside the write scope.
4. **Evidence is part of the interface.** Offline validation proves structure
   and transport logic. Only game-produced, correlated responses prove Lua
   execution. Timeout, malformed output, authentication failure, and assertion
   failure are distinct from success.

## Public contracts

The registry is authoritative for names and input schemas. Input validation
occurs before dispatch. Both adapters preserve JSON-compatible success data and
machine-readable errors; the CLI additionally returns a failing exit status.
MCP stdout contains protocol messages only. Text logs use stderr or files.

Filesystem inputs resolve within their declared roots. Read and search operations
bound work and output. Mod deployment copies a validated project into a toolkit
profile; overwriting an existing deployment must be an explicit operation.
The `mod_check` contract is structural validation of the toolkit's `42/` scaffold.
It does not select among arbitrary compatible version folders or validate all
mod.info dependency semantics, asset formats, Java integrations, or multiplayer
behavior. A structurally valid scaffold still needs real game acceptance.
Automatic retries of state-changing game requests are unsafe because a lost
response does not show whether execution occurred.

The bridge request file is `pzt-request.txt`. JSON heartbeat and response payloads
use `pzt-status.txt` and `pzt-response.txt`: the inspected Build 42.20 file-writer
extension allowlist permits `.txt` and rejects `.json`. Host-generated reports may
still use `.json`, since Python writes those files outside the game's writer API.
The request carries a token, unique request ID, expiry, and Lua code. The client
consumes it on ticks only after a player is loaded, validates the envelope, and
emits JSON evidence correlated to the request ID. Request size, response size,
and caller wait time are bounded. The bridge is limited to an explicitly enabled
local debug single-player session with both `isClient()` and `isServer()` false.
Readiness includes compiler capability: `loadstring` was disabled in 42.20.4 and
restored in 42.21. Missing compilation support produces an actionable diagnostic.
The token grants local code execution, not a Lua sandbox. Lua code must terminate;
a host-side timeout cannot interrupt arbitrary code already running on a game
tick. Keep test snippets small and use a disposable test save.

A passing scenario certifies only assertions completed synchronously during that
request. Registering a callback and returning does not wait for it or correlate
its later failures. Asynchronous completion is a separate roadmap capability.
Heartbeat and execution currently depend on `OnTick`; pausing the world can make
the heartbeat stale and prevent work from completing until the world resumes.

## Structure and development workflow

`src/pztoolkit/` owns the core, adapters, harness, and packaged bridge assets.
`tests/` owns offline behavior checks. `docs/plan.md` owns delivery checkpoints.
The root and child AGENTS.md hierarchy defines stable contribution contracts.

Windows delivery uses a standalone console `pz.exe` with embedded Python, MCP
dependencies and bridge data. CLI and MCP use that same binary (`serve` selects
stdio MCP). `packaging/build.ps1` builds it and a ZIP with config/examples;
`packaging/verify_exe.py` exercises the frozen CLI, asset deployment and MCP
protocol from a temporary directory. The frozen entry point resets the Windows
DLL directory so external game processes inherit normal DLL lookup paths.

Create a Python environment, install the package with development extras, and run
`python -m pytest`. Use the installed CLI's `--help` and tool listing as the source
of truth for runnable commands. Development tests use pytest and Lupa for local
Lua execution checks. Prefer explicit typed inputs, direct functions, and small
named helpers. Add a dependency only when the standard library or an existing
dependency cannot serve the need.

With `pztoolkit.local.json` configured for the installed game and toolkit profile,
the development loop is:

```powershell
pz --config pztoolkit.local.json tools
pz --config pztoolkit.local.json call mod_create --args-file examples/create-mod.json
pz --config pztoolkit.local.json call profile_prepare
pz --config pztoolkit.local.json call mod_deploy --args-file examples/check-mod.json
pz --config pztoolkit.local.json call game_launch
pz --config pztoolkit.local.json call bridge_status
pz --config pztoolkit.local.json call harness_run --args-file examples/smoke.json
```

UTF-8 JSON argument files avoid differences in native-command quoting between
PowerShell versions. Inline `--args` remains available when the shell preserves
the JSON string correctly.

Activate the test mods and load a disposable world before bridge checks and
scenarios. After deploying code changes, restart/load the test world to exercise
the new files. Hot reload is not part of the acceptance contract. Source tool
paths are relative to the installed `media/` root, such as `lua/...` or `scripts/...`.
Keep the configuration and generated token local and ignored by Git.

## MVP acceptance criteria

- CLI and MCP enumerate the same tools and dispatch identical validated inputs.
- Invalid inputs and paths fail before side effects.
- A generated toolkit `42/` scaffold passes local structural validation; invalid
  supported structure produces useful findings without claiming full mod validity.
- Source search/read operates only within the configured game root with bounds.
- Deployments and launch commands target a dedicated profile, with normal game
  saves and mods unaffected.
- Offline tests cover profile isolation, malformed/expired responses, correlation,
  timeouts, `.txt` wire filenames, compiler capability, single-player context,
  bounded synchronous results, and observable adapter behavior.
- A live session can activate the bridge, run a passing and failing scenario, and
  retain JSON evidence and relevant logs. Until this is exercised, report live
  game verification as outstanding.

## Boundaries

Always validate inputs, preserve local game data, and report evidence limits.
Ask only for unresolved consequential choices, unavailable access, or actions
outside the authorized scope. Never publish game assets, secrets, saves, or
tokens; never mark a simulated response as game validation.

## Compatibility and open risks

Build 42 layout, launcher arguments, mod activation, and game file APIs can vary
with updates. Inspect installed Lua and capture the installed version during live
acceptance. A request timeout has unknown execution outcome. Long-running Lua
can stall the client. Multiplayer and dedicated servers need separate trust and
execution models before bridge support is expanded.
API signatures do not guarantee every function is enabled in a particular
security hotfix. Online docs, community event notes, local source, and runtime
evidence have different authority and build applicability; keep those distinct.
Console logs may be cleared and rewritten at a size limit, so byte-offset log
excerpts can be incomplete across truncation; JSON reports remain primary evidence.

## Roadmap

Server administration adds process lifecycle, configuration validation, log
inspection, and an authenticated administration channel. Gameplay adds read-only
snapshots before bounded actions, deterministic scenario setup, and replayable
evidence. Mod development remains a complete independent workflow throughout.
Broader mod development adds dependency and version-folder resolution, Java
integration, map and asset validation, multiplayer test matrices, and optional
ZBSpec integration after checking its licensing and compatibility. Tick-driven
scenario completion must correlate deferred assertions before asynchronous tests
can count as passed. Each addition requires separate acceptance criteria.
