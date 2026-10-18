# Validation record

Checked October 17, 2026. This records evidence for the initial mod development
implementation, separately from the research findings.

| Check | Result |
| --- | --- |
| Full offline suite | 85 tests passed on local Windows, Python 3.11, including native GUI flows, contrast and result-tone reset checks |
| MCP connection | Actual stdio handshake, discovery, schema parity and invocation passed |
| Boundary cases | Invalid inputs, ownership collisions, traversal and Windows junction regressions passed |
| Harness transport | Correlation, stale responses, failure, malformed result, timeout, lock cleanup and reports passed |
| Lua bridge | 31 Lua 5.1 mock tests passed; these are not Kahlua client execution |
| Research changes | Allowed extensions, missing compiler, network guards, launch arguments and log rollover covered |
| Dependencies | Frozen lock check and installed-package compatibility check passed |
| Packaging | Source distribution and wheel built; required bridge/common assets found in wheel |
| Windows executable | PyInstaller 6.22.3 single-file `pz.exe` built; CLI discovery, bundled bridge deployment, actual MCP handshake, schema parity, invocation and invalid input verified from a temporary working directory |
| Native GUI | Real Tk widget flows cover setup validation, mod creation/check/deploy, saved scenario editing, trust gating, background responsiveness, pass/fail/timeout reports and cross-workspace discard safety |
| Frozen desktop smoke | Windowed PE subsystem, actual mapped Tk window, three page controls, private font, artwork, background dispatch and bundled bridge deployment passed from a temporary directory |
| Earlier GUI visual inspection | The initial pale window was inspected through Computer Use; mod/scenario controls fit and bridge diagnostics worked |
| Horror theme | Corrected empty-facility artwork and distressed studio mark inspected; source review and automated contrast/font checks passed. Current rendered appearance at default/minimum sizes remains unverified after the user stopped desktop control |
| Local CLI smoke | Doctor, profile preparation, sample scaffold/check/deploy passed |
| Real game startup | Windows client process launched with isolated cachedir, debug and mods-only discovery |
| Runtime startup artifacts | Isolated console/OpenGL initialization and version file created, reporting 42.20.0, revision a2947723ca |
| First-launch activation | Observed default mod list cleared by first-launch reset, matching source research |
| In-world assertions | Not yet verified; requires enabling bridge/sample and entering a disposable unpaused world |

The running test instance uses the ignored `.local/profile/` directory. Its
full logs, configuration, generated mods and token are not published. Startup is
partial live evidence; it does not establish bridge activation or a passing
scenario.

The sample `HelloZomboid` mod and smoke scenario were generated locally. Next:
enable **PZ Toolkit Bridge** and **HelloZomboid**, create a fresh single-player
world, keep it unpaused, check `bridge_status`, then run `examples/smoke.json`.

The bridge reports ordinary Lua errors as failed scenarios but cannot preempt a
running infinite loop, certify deferred callbacks, or suppress every game-side
debugger/error presentation. A timeout is inconclusive. Console excerpts are
bounded best-effort evidence with rollover/capture-limit flags.

The DOX closeout updated root, package, test and GUI-asset contracts and child
indexes. `docs/AGENTS.md` remains unchanged because documentation ownership and
evidence rules already cover these records.

The [GitHub workflow run](https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39084742653)
passed all four jobs on Windows and Linux with Python 3.11 and 3.12 for
implementation commit `c6d5aea`. Each job verified the frozen lock, installed
dependencies, checked dependency compatibility, compiled Python sources and ran
the offline suite. This verifies the offline implementation across that matrix;
it does not replace in-world game acceptance.
