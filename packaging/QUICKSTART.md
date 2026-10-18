# Project Zomboid Toolkit for Windows

Open **PZToolkit/PZToolkit.exe**, or find **Project Zomboid Toolkit** in the Start menu
under **Dead Signal Interactive**. No terminal or Python installation is needed.

This is a connection to the game for you and Codex. You do not need to make a
mod, select project folders or create a test-script file.

The app starts on **Offline tools**. The game can stay closed:

1. Choose **Read game logs** to see saved test-profile history, or **Check settings**
   to inspect the saved installation. No log yet is normal.
2. Type a word or phrase and choose **Search scripts**.
3. Select a result, then **Read script**. These are read-only excerpts from the
   installed game, not changes to your mod.

Script tools need the installed game files at the saved location. Log reading needs
an existing test-profile log. Neither needs a live game connection.

For live controls only:

1. Open **Connection** and choose **Connect to game**. It installs **PZ Toolkit
   Bridge** if needed and checks the connection, using your saved settings.
2. If the test game is closed, choose **Launch Project Zomboid (test profile)**.
3. In the game, enable **PZ Toolkit Bridge** and your existing mod in Mods.
   Load a debug single-player world and unpause it.
4. Choose **Check connection**, then open **Game tools** for god mode or editors.

God mode and editor buttons need a ready bridge in a loaded, unpaused debug
single-player world. The main menu and paused worlds do not qualify. When the
app says **Game closed** or **Live game not connected**, offline tools stay usable.
Do not relaunch a test game that is already running; check its connection instead.

Debug starts with the game. God mode turns on when your character loads or
respawns with the bridge enabled. You can switch it off for damage tests.
The existing separate test settings and saves are preserved; your normal saves
are not moved or replaced. Restart an existing game session to load an updated
bridge helper.

Keep both complete application folders, including their `_internal` support
directories. Copying an EXE alone does not install this version.

For Codex or another MCP client, set the executable to the installed **pz/pz.exe**
and arguments to `["serve"]`. The app and MCP use the same saved connection at
`%LOCALAPPDATA%/PZToolkit/config.json`. An explicit `--config` is available for
existing integrations, but normal use needs no folder wizard.

The advanced Lua control additionally needs the game build's Lua compiler.
It sends code directly to the loaded world and needs no scenario file. Review and trust code before sending it. A timeout cannot cancel
Lua already running. Editor requests are not proof that a window appeared.

Offline packaging checks do not establish live game acceptance. Current evidence
and source: https://github.com/raiinman/project-zomboid-toolkit

On Build 42.20.4, god mode and built-in editor commands work without a Lua
compiler. Custom Lua is unavailable in that build; the app explains this
separately from the game connection.
