<h1 align="center">Project Zomboid Toolkit</h1>
<p align="center">A Dead Signal Interactive game bridge, desktop toolbelt, CLI and MCP server.</p>
<p align="center">
  <img alt="Status: preview" src="https://img.shields.io/badge/status-preview-orange">
  <img alt="Target: Build 42" src="https://img.shields.io/badge/target-Build_42-9c714d">
  <img alt="Windows app" src="https://img.shields.io/badge/app-Windows-blue">
</p>
<p align="center"><a href="docs/design.md">Architecture</a> Â· <a href="docs/plan.md">Delivery plan</a> Â· <a href="docs/validation.md">Validation</a> Â· <a href="docs/skills.md">Skills</a> Â· <a href="AGENTS.md">Agent guidance</a></p>

<p align="center"><strong>v0.4.1 remains blocked.</strong> Defender quarantined its CLI. Do not restore it or add an exclusion. The clean CI-built v0.4.2 bundle passed an ordinary Defender scan on the development PC and is installed there with verified MCP transport. It remains unsigned; public downloads are withheld pending remaining release checks. See <a href="docs/validation.md">validation evidence</a>.</p>

Use the toolkit with the game closed to read saved logs, search and read installed
game scripts, or check saved settings. Connect Codex or another MCP client when
you need live controls such as god mode or the built-in game editors. **You do not need to create a mod, choose project folders or save a
scenario.** Keep editing your existing mod in your editor. The game's own Mods
menu remains responsible for enabling mods.

## Open and use offline tools

Windows downloads are currently withheld pending the checks above. Version 0.4.2
uses a complete application bundle, including support files.
Installed copies have a Start menu
entry under **Dead Signal Interactive**. No terminal or Python installation is
needed to use the app.

1. Open the app. **Offline tools** is the starting page and uses your saved settings.
2. Choose **Read game logs** or **Check settings**. Logs describe a saved session;
   no log yet is normal.
3. Enter a word or phrase and choose **Search scripts**. Select a result, then
   choose **Read script** to see an excerpt. Installed game files stay read-only.

No running game or bridge connection is needed for these tools. Script tools need
an installed game at the saved location; logs need an existing isolated-profile log.
Checking settings reports missing files without launching the game.

## Connect for live controls

1. Open **Connection**, then choose **Connect to game**. It installs **PZ Toolkit
   Bridge** if needed and checks the connection.
2. If the test game is closed, choose **Launch Project Zomboid (test profile)**.
   In the game's Mods menu, enable **PZ Toolkit Bridge** and your existing mod.
3. Load a debug single-player world and unpause. Choose **Check connection**.
4. Open **Game tools** for god mode and the built-in editors.

**Game closed** or **Live game not connected** does not block offline tools.
Live buttons stay disabled until a ready bridge is reported. A game at the main
menu, a paused world or an ordinary game without the bridge is not a ready connection.

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

Set the client's executable to your installed **pz.exe** and select the saved
connection explicitly before **serve**.
Both the app and CLI use the saved connection settings at
`%LOCALAPPDATA%/PZToolkit/config.json` by default.

```json
{
  "mcpServers": {
    "project-zomboid": {
      "command": "C:/path/to/installed/pz.exe",
      "args": ["--config", "C:/Users/your-name/AppData/Local/PZToolkit/config.json", "serve"]
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

| Tool | Purpose | Needs a running game? |
| --- | --- | --- |
| `doctor` | Check saved settings and the installation | No |
| `bridge_install` | Install or refresh the bridge helper, preserving its token and backing up changed files | No, stop the tracked test game before helper changes |
| `game_launch` | Open the installed game with debug and the existing isolated profile | Starts the game |
| `bridge_status` | Check a fresh loaded-world connection and actual god-mode state | No for checking; a ready result needs a loaded world |
| `logs_read` | Read saved game logs from the isolated profile | No |
| `source_search`, `source_read` | Search or read installed Lua and scripts without changing them | No |
| `lua_execute` | Run trusted inline Lua without creating a scenario or report file | Loaded, unpaused debug single-player bridge and Lua compiler |
| `god_mode` | Set and verify the loaded character's god mode | Loaded, unpaused debug single-player bridge |
| `debug_editors` | List supported built-in game editors | No, listing only |
| `editor_open` | Request the debug, vehicle, attachment, animation or world-map editor | Loaded, unpaused debug single-player bridge |

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
Build 42.20.4 supports predefined god-mode/editor commands but removes custom
Lua compilation; the app reports that capability separately from connection.

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
./packaging/scan.ps1 -BundlePath dist/pz-windows -BuildReceipt dist/build-receipt.json -ReceiptPath dist/scan-receipt.json
uv run --no-sync python packaging/verify_exe.py dist/pz-windows/pz/pz.exe dist/scan-receipt.json
uv run --no-sync python packaging/verify_gui.py dist/pz-windows/PZToolkit/PZToolkit.exe dist/scan-receipt.json
```

Use clean Windows CI for candidate builds. See [Windows distribution](docs/windows-release.md)
for the blocked release, provenance, trusted-signing prerequisite and scan gates.
The build produces complete GUI/CLI application folders and a Windows ZIP. Offline tests,
executable checks, rendered window review and real in-game acceptance are separate
forms of evidence. Current results and outstanding live checks are recorded in
[validation](docs/validation.md) and the [delivery plan](docs/plan.md).

Four broad research passes and four additional PZWiki passes informed the bridge:
[research](docs/research.md), [wiki findings](docs/wiki-research.md), and
[coverage ledger](docs/wiki-coverage.csv). Partial/index/excluded coverage is explicit.
The project uses the [DOX framework](https://github.com/raiinman/dox) and relevant
workflows from the user's [skill library](https://github.com/raiinman/skill-library).
See [provenance](docs/skills.md) and the preserved [MIT notice](docs/DOX-LICENSE).
