<h1 align="center">Project Zomboid Toolkit</h1>
<p align="center">Windows desktop app, MCP and CLI, with an in-game Lua test harness.</p>
<p align="center">
  <img alt="Status: initial mod development implementation" src="https://img.shields.io/badge/status-initial_implementation-orange">
  <img alt="Target: Build 42" src="https://img.shields.io/badge/target-Build_42-green">
  <img alt="Python: 3.11 or later" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>
<p align="center"><a href="docs/design.md">Design</a> · <a href="docs/plan.md">Delivery plan</a> · <a href="docs/skills.md">Skills and provenance</a> · <a href="AGENTS.md">Agent guidance</a></p>

The first milestone supports **mod development**. One Python registry defines all
11 tools, their JSON input schemas, validation, and execution. The CLI and MCP
server consume that registry. A companion Lua mod receives scenarios inside a
running debug single-player game and returns assertion results.

Server administration and gameplay automation remain later milestones.

## Setup

Download [the Windows ZIP](https://github.com/raiinman/project-zomboid-toolkit/releases/download/v0.2.0/pz-windows.zip),
extract it, and double-click **PZToolkit.exe**. It opens a proper desktop window;
no terminal or Python installation is needed.

1. **Setup:** choose your game, workspace and isolated test profile. Save setup,
   then prepare the test profile.
2. **Mods:** create a mod, select it, check it and deploy it. Open its folder to
   edit the mod sources with your preferred editor.
3. **In-game tests:** launch the game, check bridge readiness, select and edit
   a scenario, save it, then run it. Results, logs and reports are available in
   the window. Enable the bridge and your mod in a loaded, unpaused disposable
   single-player world first.

The app saves its configuration in `%LOCALAPPDATA%/PZToolkit/config.json` by
default. Setup shows the active file and can open an existing toolkit config.
Unsaved settings must be saved before tool actions. One background action runs
at a time, keeping the window responsive while the game returns a result.

The desktop uses a distressed **Dead Signal Interactive** identity, a dark
industrial horror palette and an empty abandoned-facility header. There are no
creature figures in the artwork. The theme preserves native controls and literal
test outcomes. Its visual contract is in [DESIGN.md](DESIGN.md).

Live testing requires your own Project Zomboid installation. The launcher targets
Windows and Build 42. **pz.exe** remains a separate console CLI and MCP server.
The following commands are optional alternatives to using the app:

```powershell
Copy-Item pztoolkit.example.json pztoolkit.local.json
.\pz.exe call doctor
.\pz.exe tools
```

Edit `game_dir` in `pztoolkit.local.json` to your game installation. Relative paths
resolve beside the config file. `profile_dir`, `workspace_dir`, and `game_dir` must
be disjoint. Use a new toolkit profile, outside your normal `Zomboid` directory.
Local configuration, profiles, tokens, game logs, and reports are ignored by Git.

## First mod and in-game test

Examples read JSON argument files so shell quoting works consistently.

```powershell
.\pz.exe call profile_prepare
.\pz.exe call mod_create --args-file examples/create-mod.json
.\pz.exe call mod_check --args-file examples/check-mod.json
.\pz.exe call mod_deploy --args-file examples/check-mod.json
.\pz.exe call game_launch
```

First launch may clear the prepared default mod list. In the isolated game window,
confirm **PZ Toolkit Bridge** and **HelloZomboid** are
enabled under Mods. Create a disposable single-player world with both mods enabled.
Once your character is loaded and the game is running:

```powershell
.\pz.exe call bridge_status
.\pz.exe call harness_run --args-file examples/smoke.json
.\pz.exe call logs_read --args-file examples/logs.json
```

`mod_create` writes `projects/mods/HelloZomboid/42/mod.info`, a client Lua file,
a `common/` directory, and `projects/scenarios/HelloZomboid_smoke.lua`.
Edit the mod and scenario files with your editor or coding agent. Redeploy and
restart/load the test world after mod changes. Deployment preserves the previous
copy under the isolated profile's `backups/` directory.

Scenario files contain ordinary Lua assertions and may return a message. An
exception or `return false` fails the scenario. Every completed harness wait writes
a JSON report containing request ID, scenario SHA256, result, duration, and new
console output under the isolated profile's `reports/` directory. A missing or
stale bridge is a setup error. A timeout is inconclusive and returns a nonzero exit.

**Run trusted, terminating scenarios only.** Lua runs with game privileges on the
game thread. The harness wait timeout cannot stop code that already started.
This bridge is for a disposable local debug single-player session. It rejects
requests when connected as a multiplayer client.

## MCP connection

Configure your MCP client to launch the executable with absolute paths:

```json
{
  "mcpServers": {
    "project-zomboid": {
      "command": "C:/path/to/project-zomboid-toolkit/pz.exe",
      "args": [
        "--config", "C:/path/to/project-zomboid-toolkit/pztoolkit.local.json",
        "serve"
      ]
    }
  }
}
```

This is a generic MCP client example. The executable includes MCP support.
The server communicates over stdio and reserves stdout for MCP messages.
It uses the official Python MCP SDK 1.x, pinned by `uv.lock`.

## Tools

| Tool | Purpose |
| --- | --- |
| `doctor` | Inspect configuration and installation |
| `source_search`, `source_read` | Search/read installed Lua and script text |
| `mod_create`, `mod_check` | Scaffold and check Build 42 mod metadata/layout |
| `profile_prepare` | Prepare an isolated profile and bridge |
| `mod_deploy` | Copy a mod into that profile with deployment backups |
| `game_launch` | Launch the Windows client using the isolated cache directory |
| `bridge_status` | Check a fresh in-world bridge heartbeat |
| `harness_run` | Execute a trusted Lua scenario and retain evidence |
| `logs_read` | Read the isolated console log |

Use `pz tools` for exact schemas. `mod_check` checks layout and metadata; it does
not claim to compile Lua or verify compatibility. Installed game source is read-only
and is never bundled or uploaded by these tools.

## Verification

Source development and executable builds require Python 3.11+ and
[uv](https://docs.astral.sh/uv/). These are build dependencies, not requirements
for users of the executable. To build on Windows:

```powershell
.\packaging\build.ps1
uv run --no-sync python packaging/verify_exe.py dist/pz.exe
uv run --no-sync python packaging/verify_gui.py dist/PZToolkit.exe
```

The outputs are `dist/PZToolkit.exe` (desktop app), `dist/pz.exe` (CLI/MCP) and
`dist/pz-windows.zip` (both executables, config template, examples and quickstart).
Extract the ZIP before following Setup.
Keep the configuration and scenario files outside
the executable. Relative configuration paths resolve beside the config file;
the default config is found in the current working directory. For source tests:

```powershell
uv sync --frozen --extra mcp --extra dev --python 3.11
uv lock --check
uv pip check
uv run --no-sync python -m pytest -q
uv build
```

Tests include actual MCP stdio discovery/invocation, filesystem containment,
deployment ownership, stale response handling, and Lua 5.1 bridge mocks.
The local suite passed 85 tests, including native GUI flows and theme checks. Startup was checked against an isolated 42.20.0
client; in-world bridge assertions remain pending. See the measured
[validation record](docs/validation.md) and [delivery plan](docs/plan.md).
The current theme's rendered finish review is pending after desktop control was
stopped; source, asset and automated contrast checks are separate evidence.

Four broad internet passes and four additional PZWiki passes informed the design:
[research](docs/research.md), [wiki findings](docs/wiki-research.md), and
[page-by-page coverage](docs/wiki-coverage.csv). The ledger accounts for 173 hub
links plus selected drill-downs, with partial/index/excluded entries explicit.

The project includes the [DOX framework](https://github.com/raiinman/dox) as an
`AGENTS.md` hierarchy and records applied workflows from your
[skill library](https://github.com/raiinman/skill-library) in
[skills and provenance](docs/skills.md). DOX's MIT notice is preserved in
[docs/DOX-LICENSE](docs/DOX-LICENSE).
