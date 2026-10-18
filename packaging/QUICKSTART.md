# Project Zomboid Toolkit for Windows

Open **PZToolkit.exe**, or find **Project Zomboid Toolkit** in the Start menu
under **Dead Signal Interactive**. No terminal or Python installation is needed.

This is a connection to the game for you and Codex. You do not need to make a
mod, select project folders or create a test-script file.

1. Choose **Connect to game**. It installs **PZ Toolkit Bridge** if needed and
   checks the connection.
   Your saved connection settings are used automatically.
2. Choose **Launch Project Zomboid (test profile)**.
3. In the game, enable **PZ Toolkit Bridge** and your existing mod in Mods.
   Load a single-player world and unpause it.
4. Return here and check the connection. Open **Game tools** to use god-mode controls, built-in
   editors or game logs. The app explains what to do if the connection is missing.

Debug starts with the game. God mode turns on when your character loads or
respawns with the bridge enabled. You can switch it off for damage tests.
The existing separate test settings and saves are preserved; your normal saves
are not moved or replaced. Restart an existing game session to load an updated
bridge helper.

For Codex or another MCP client, set the executable to the installed **pz.exe**
and arguments to `["serve"]`. The app and MCP use the same saved connection at
`%LOCALAPPDATA%/PZToolkit/config.json`. An explicit `--config` is available for
existing integrations, but normal use needs no folder wizard.

The advanced Lua control sends code directly to the loaded game. It needs no
scenario file. Review and trust code before sending it. A timeout cannot cancel
Lua already running. Editor requests are not proof that a window appeared.

Offline packaging checks do not establish live game acceptance. Current evidence
and source: https://github.com/raiinman/project-zomboid-toolkit

On Build 42.20.4, god mode and built-in editor commands work without a Lua
compiler. Custom Lua is unavailable in that build; the app explains this
separately from the game connection.
