# Validation record

## v0.4.0 direct game toolbelt

Checked October 17, 2026. Offline checks and real-game acceptance are separate.

| Check | Evidence |
| --- | --- |
| Shared interface | Default CLI and MCP expose the same 11 game tools and schemas. Actual stdio initialize, discovery and invocation pass. Legacy authoring tools require explicit `--all-tools`. |
| Inline commands | Fixed authenticated/correlated wire transport, timeout cleanup, strict arguments, allowlisted editor IDs and no workspace/scenario/report creation verified with fixtures. |
| Running-game protection | Installing or refreshing the helper refuses a tracked running game before changing files. Two regression cases verify no mutation. |
| Startup god mode | 46 Lua 5.1 mock cases cover spawn/respawn/tick fallback, local debug authentication guards, actual-state reporting, API failures and later manual disable. These are not native Kahlua execution. |
| Native widgets | Connection/Game tools, shared dispatch, readiness gating, inline trust, beginner instructions and minimum-size widget bounds have offline Windows Tk coverage. Final rendered visual acceptance is pending. |
| Game API basis | Read-only shipped `ISDebugMenu.lua` confirms debug, vehicle, attachment, animation and world-map entry points. `ISAdminPowerUI.lua` confirms `setGodMod`/`isGodMod`; TutorialSetup/ISPlayerData confirm index-only player creation events. |
| Brand | Approved distressed logo PNG bytes preserved. Original derelict-workshop image generated with its prompt embedded and separately saved. No green or creature art in the new interface. |
| Actual PC baseline | Remote Desktop Commander verified the saved game connection and owned isolated profile. Game was closed; no live bridge heartbeat was present. |

The final local Windows/Python 3.11 suite passed: **161 tests**, including 27
native-widget cases and 46 Lua mocks. Frozen lock, dependency compatibility and
independent source review passed. Both review findings (tracked-game helper
refresh and repeated Lua trust invalidation) were fixed and covered.
Both v0.4.0 frozen binaries passed verification: console CLI, bundled helper,
actual MCP initialize/discovery/schema/invocation and invalid-input checks;
windowed PE header, mapped fixture Tk window, both pages, Lua controls,
minimum-size bounds, font and assets. This is an automated fixture smoke check,
not a new visual inspection of the installed app.
Actual-PC installation results follow as each completes.
No source or fixture success establishes a connected world.

## Acceptance still pending

- Final rendered GUI review. The user stopped desktop control with Escape;
  no subsequent native input, captures or window activation were attempted.
- A loaded, unpaused single-player world confirming startup god mode, current
  debug/connection state and each built-in editor opening visibly.
- Live inline command execution and game assertion evidence.

Editor results mean a request completed, not that its window was visibly
observed. Heartbeats can become stale while paused. A timeout is inconclusive.
The bridge cannot preempt an infinite Lua loop or certify deferred callbacks.

## Earlier releases

Versions 0.3.0 through 0.3.2 passed their Windows/Linux Python 3.11/3.12 CI
matrices and frozen executable checks. The earlier mod/folder/scenario GUI
was installed and partly inspected, but that visual evidence does not apply
to this replacement toolbelt. Historical detailed records remain in Git.

- [v0.3.0 CI](https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39089375898)
- [v0.3.1 CI](https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39090296966)
- [v0.3.2 CI](https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39092850254)

Earlier client startup produced isolated runtime artifacts for Build 42.20.0,
revision a2947723ca. That only established startup, not in-world execution.

## DOX closeout

Root, source, test and GUI asset contracts reflect the direct toolbelt. The
`docs/AGENTS.md` ownership, index and evidence rules remain valid and are
intentionally unchanged. No user mod, normal save or installed game content
is part of the toolkit source changes.
