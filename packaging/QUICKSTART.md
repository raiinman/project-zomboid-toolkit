# Project Zomboid Toolkit for Windows

Extract the ZIP into its own folder. `pz.exe` is a standalone console application
with the Python runtime and MCP support included. You do not need to install Python.

Open PowerShell in that folder:

```powershell
Copy-Item pztoolkit.example.json pztoolkit.local.json
.\pz.exe call doctor
.\pz.exe tools
```

Edit `game_dir` in `pztoolkit.local.json` for your installed game. Keep the
isolated profile outside your normal Zomboid saves and mods. Configuration paths
resolve beside the config file. The default config is found in your current
working directory; use `--config C:/absolute/path/pztoolkit.local.json` elsewhere.

```powershell
.\pz.exe call profile_prepare
.\pz.exe call mod_create --args-file examples/create-mod.json
.\pz.exe call mod_deploy --args-file examples/check-mod.json
.\pz.exe call game_launch
```

Enable PZ Toolkit Bridge and HelloZomboid in the isolated game, enter a disposable
single-player world and unpause it. Then:

```powershell
.\pz.exe call bridge_status
.\pz.exe call harness_run --args-file examples/smoke.json
```

Run only trusted, terminating Lua scenarios. Timeout cannot cancel Lua already
running in the game. In-world assertions have not yet been verified against the
installed game. The executable packaging checks do not establish game acceptance.

For MCP, set your client's command to the absolute `pz.exe` path and arguments to
`["--config", "C:/absolute/path/pztoolkit.local.json", "serve"]`.

Source, research and full documentation:
https://github.com/raiinman/project-zomboid-toolkit
