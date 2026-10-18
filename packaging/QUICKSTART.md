# Project Zomboid Toolkit for Windows

Extract the ZIP into its own folder and double-click **PZToolkit.exe**. It opens
the desktop app without a terminal. Python is bundled; no separate installation
is needed.

The sidebar selects **Mods**, **In-game tests** and **Setup**. Leave **Show guide**
enabled for eight short steps with arrows pointing at the next control. **Show me**
opens the relevant page; **Previous** and **Next** revisit instructions without
running actions. Successful actions advance the matching step. Resize the
activity/results dock by dragging its divider when you need more output space.

1. In **Setup**, choose your game installation, mod workspace and a new isolated
   test profile. Choose **Save setup**, then **Prepare test profile**.
2. In **Mods**, enter a mod ID, choose **Create mod**, then select it and choose
   **Check selected** and **Deploy to test profile**. **Open mod folder** opens
   its source files in Explorer for editing with your preferred editor.
3. In **In-game tests**, choose **Launch test game**. Enable **PZ Toolkit Bridge**
   and your mod in the game's Mods menu. Enter a disposable single-player world
   and unpause it.
4. Choose **Check bridge**, select a generated scenario, review or edit the Lua,
   and save your changes. Select the trust checkbox, then **Run saved scenario**.
   Results appear in the window. **Read game logs** and **Open reports** show
   the captured evidence.

App settings are stored in `%LOCALAPPDATA%/PZToolkit/config.json` by default.
Use **Open config** to share an existing CLI/MCP configuration. The active
settings file is shown in Setup. Keep the isolated profile outside normal
Zomboid saves and mods. Relative folders resolve beside the configuration file.

The separate **pz.exe** retains the CLI and MCP server for scripts and AI clients.
For optional CLI use, pass the settings path shown in the app:

```powershell
.\pz.exe --config "$env:LOCALAPPDATA/PZToolkit/config.json" tools
```

Run only trusted, terminating Lua scenarios. Timeout cannot cancel Lua already
running in the game. In-world assertions have not yet been verified against the
installed game. The executable packaging checks do not establish game acceptance.

For MCP, set your client's command to the absolute `pz.exe` path and arguments to
`["--config", "C:/absolute/path/pztoolkit.local.json", "serve"]`.

Source, research and full documentation:
https://github.com/raiinman/project-zomboid-toolkit
