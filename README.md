<h1 align="center">Project Zomboid Toolkit</h1>
<p align="center">A Dead Signal Interactive game bridge, desktop toolbelt, CLI and MCP server.</p>
<p align="center">
  <img alt="Status: preview" src="https://img.shields.io/badge/status-preview-orange">
  <img alt="Target: Build 42" src="https://img.shields.io/badge/target-Build_42-9c714d">
  <img alt="Windows app" src="https://img.shields.io/badge/app-Windows-blue">
</p>
<p align="center"><a href="docs/design.md">Architecture</a> · <a href="docs/plan.md">Delivery plan</a> · <a href="docs/validation.md">Validation</a> · <a href="docs/skills.md">Skills</a> · <a href="AGENTS.md">Agent guidance</a></p>

Connect Codex or another MCP client to your running Project Zomboid debug world.
Use the desktop app to connect, change god mode, open built-in debug editors and
read logs. **You do not need to create a mod, choose project folders or save a
scenario.** Keep editing your existing mod in your editor. The game's own Mods
menu remains responsible for enabling mods.

## Open and connect

Download [the Windows ZIP](https://github.com/raiinman/project-zomboid-toolkit/releases/download/v0.4.0/pz-windows.zip),
extract it and open **PZToolkit.exe**. Installed copies also have a Start menu
entry under **Dead Signal Interactive**. No terminal or Python installation is
needed to use the app.

1. Open the app. It uses your existing saved connection settings.
2. Choose **Connect to game**. It installs **PZ Toolkit Bridge** if needed and
   checks the connection.
3. Choose **Launch Project Zomboid (test profile)**. In the game's Mods menu,
   enable **PZ Toolkit Bridge** and any existing mod you want to work on.
4. Load a single-player world and unpause. Return to the app and check the
   connection. The app reports whether the bridge and god mode are ready.
5. Use the game tools, or connect Codex using the MCP example below.

The test profile is the existing separate set of game settings and saves.
The app keeps that safety boundary and does not create another mod project or
move your existing workspace. Debug is enabled at launch. With the bridge enabled,
god mode turns on when your character loads or respawns. You can turn it off
for damage tests. The bridge reports its actual state rather than assuming it.

The interface keeps the approved distressed Dead Signal Interactive logo,
charcoal surfaces and warm derelict-workshop artwork. Help explains the next
connection step; technical details start closed and inline Lua has a separate advanced tab.
The visual contract is in [DESIGN.md](DESIGN.md).

## Connect Codex or another MCP client

Set the client's executable to your installed **pz.exe** and pass **serve**.
Both the app and CLI use the saved connection settings at
`%LOCALAPPDATA%/PZToolkit/config.json` by default.

```json
{
  "mcpServers": {
    "project-zomboid": {
      "command": "C:/path/to/installed/pz.exe",
      "args": ["serve"]
    }
  }
}
```

Replace the example executable path with the installed location. An existing
configuration can be selected explicitly with `--config` before `serve`.
The server uses stdio, reserving stdout for MCP messages. The standalone
executable includes the official Python MCP SDK 1.x, pinned by `uv.lock`.

## Shared game tools

The normal desktop, CLI and MCP surface uses the same 11-tool registry view.

| Tool | Purpose |
| --- | --- |
| `doctor` | Check saved settings and the installation |
| `bridge_install` | Install or refresh the bridge helper, preserving its token and backing up changed files |
| `game_launch` | Open the installed game with debug and the existing isolated profile |
| `bridge_status` | Check a fresh loaded-world connection and actual god-mode state |
| `logs_read` | Read game logs from that profile |
| `source_search`, `source_read` | Search or read installed Lua and scripts without changing them |
| `lua_execute` | Run trusted inline Lua without creating a scenario or report file |
| `god_mode` | Set and verify the loaded character's god mode |
| `debug_editors` | List supported built-in game editors |
| `editor_open` | Request the debug, vehicle, attachment, animation or world-map editor |

An editor request returning successfully does not prove its window is visible.
This toolbelt does not claim UEFN Toolbelt feature parity. More game capabilities
can be added through the same registry.

For optional CLI use:

```powershell
.\pz.exe tools
.\pz.exe call bridge_status
.\pz.exe serve
```

Use `tools` for current schemas. The older file/scaffold operations remain
available for existing scripts through `pz.exe --all-tools ...`; they are not
part of normal onboarding or the GUI. The complete legacy registry has 17 tools.

## Execution limits

The bridge runs in a loaded, unpaused local debug single-player world. It refuses
multiplayer client and server contexts. Lua has game privileges and must terminate;
a timeout cannot stop code already running and means the outcome is unknown.
Only synchronous assertions contribute to a result. Use trusted commands.

Inline commands reuse bounded authenticated request/response files inside the
existing profile. They do not create scenario or per-command report files.
Normal saves, installed game sources and unrelated mods stay outside toolkit
writes. Local settings, tokens, game files and logs stay out of Git.

## Development and verification

Building requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). App users do
not need either installed.

```powershell
uv sync --frozen --extra mcp --extra dev --python 3.11
uv run --no-sync python -m pytest -q
.\packaging\build.ps1
uv run --no-sync python packaging/verify_exe.py dist/pz.exe
uv run --no-sync python packaging/verify_gui.py dist/PZToolkit.exe
```

The build produces the GUI, CLI/MCP executable and Windows ZIP. Offline tests,
executable checks, rendered window review and real in-game acceptance are separate
forms of evidence. Current results and outstanding live checks are recorded in
[validation](docs/validation.md) and the [delivery plan](docs/plan.md).

Four broad research passes and four additional PZWiki passes informed the bridge:
[research](docs/research.md), [wiki findings](docs/wiki-research.md), and
[coverage ledger](docs/wiki-coverage.csv). Partial/index/excluded coverage is explicit.
The project uses the [DOX framework](https://github.com/raiinman/dox) and relevant
workflows from the user's [skill library](https://github.com/raiinman/skill-library).
See [provenance](docs/skills.md) and the preserved [MIT notice](docs/DOX-LICENSE).
