# Validation record

## v0.4.2 installed Windows candidate

The clean-build/provenance, optional trusted-signing and normal Defender scan
gates passed independent source review. The full local suite passed **215
tests**, including 28 packaging fixtures. The final folder-tag helper fix then
passed all 30 focused packaging cases. Candidate execution occurred only after
the actual-PC scan described below. GUI executable probes remain deferred.

CI run `39098858667` passed the clean Windows build and native-origin gate,
but stopped before scanning because the runner lacked active/current Defender
protection. It produced no antivirus verdict and ran no candidate executable.
The PC has active, current Defender in Normal mode. A harmless text-file scan
confirmed scanner permission and correlated custom-scan events; this does not
clear an application candidate. Offline regression fixtures now cover Defender's
`file:_` resource format, delayed publication and unrelated quick-scan events.

The user confirmed no signing identity exists. Candidates remain unsigned;
trusted publisher signing cannot be completed without external enrollment.
The blocked v0.4.1 release has a visible security-review warning.

Clean CI run `39099328529` built implementation commit
`d18977f122065f602f0fb0b4530c9f57c57fc4fb` with native-origin verification.
All four offline test jobs passed their test steps, but the Windows packaging
job remains failed because hosted Defender was unavailable. Frozen CI probes
were skipped; no green CI or rendered GUI result is implied.

On the actual PC, ordinary Defender scanning of the unchanged extracted bundle
and ZIP passed at `2026-10-18T05:09:40Z`, using engine `1.1.26090.9` and
signatures `1.461.79.0` in Normal mode. Scan event pairs `26745/26746` and
`26747/26748` correlate the exact folder and ZIP. No new/changed detections or
file hashes were observed. ZIP SHA-256:
`462C0F6F3EED3648231BE42080B713E3F29EDBDA55DC7DC873B0397CB9B6E9D3`.
The external scan helper accepts the PC's observed `folder:_` tag. Its focused
suite passes 30 packaging cases; the candidate application bytes were unchanged.
Receipts remain in private app-owned staging. This is point-in-time clearance,
not trusted signing or a determination about the old detection.

A bounded authenticated predefined command was sent directly through the
already-running game bridge, without executing the quarantined CLI. The game
returned correlated success, `God mode enabled`, after actual readback.
This completes native god-mode enable verification on 42.20.4. Editor/mod tests
are deferred to Javelin work.

After the successful scan, the installer copied the complete byte-identical
bundle, reverified all installed files and ZIP members, updated the existing
Start menu target and enabled global `project-zomboid` MCP registration.
Configuration and bridge-token SHA-256 values are unchanged. Unrelated MCP
definitions compare equal after canonicalizing JSON key order. An interrupted
registration attempt rolled back before the verified retry; no quarantined
binary was restored. The GUI and game were not launched, activated or controlled.

At `2026-10-18T05:23:04Z`, the installed `pz.exe serve` passed a hidden real
stdio MCP initialize/list/call probe: the exact 11-tool registry, `doctor`,
`bridge_status` and `debug_editors` succeeded. Fresh game status reports
`ready=true`, `debug=true`, `god_mode=true` and built-in operations available.
Custom Lua remains unavailable on this build. Editor IDs were discovered without
opening editors or changing the game. The probe shut down its own server process.
This chat subsequently discovered the native MCP namespace, but direct `doctor`
and `bridge_status` calls exposed cached settings for an old development profile
and a stale 42.20.0 heartbeat. The verified installed-app connection is now pinned
explicitly with `--config` in MCP registration. Only the identified stale stdio
process was stopped. The host currently reports `Transport closed` and requires
its app-side server Restart control; native chat readiness remains pending.
After the probe, the installed CLI still exists with SHA-256
`3F0EDBC0E9658629AF70610C337C94C22774C1480B33DB68517778B198987E2C`.
There are zero new Defender 1116/1117 events after scan completion, and protection
remains active and current in Normal mode.

DOX closeout updated release/validation guidance, scan-helper and test contracts,
and the no-desktop-control preference. Source/game/asset contracts and child
indexes remain unchanged because this recovery changes packaging and installation,
not their behavior or ownership. No new rendered GUI acceptance is claimed.

## v0.4.1 compatibility update

Subsequent PC inspection found that Microsoft Defender quarantined the v0.4.1
console `pz.exe` as `Trojan:Win32/Bearfoos.A!ml`. Earlier hash/protocol checks
remain historical evidence, not proof of current MCP availability or a false
positive. The flagged executable has not been restored, allowed or excluded.
At discovery, direct MCP calls failed because that installed file was missing.

The user clarified the cursor is missing from game startup, not only while
aiming. With the game closed, the isolated profile's display settings were
backed up and changed to ordinary windowed 1600x900 for verification. Normal
profile settings were untouched. Editor/mod checks are deferred to Javelin
development at the user's request.

Both frozen executable probes passed. The published v0.4.1 ZIP and installed
binaries were hash verified on the actual PC. Existing configuration/token
were preserved, and Start menu plus enabled Codex MCP point to v0.4.1.
The installed default Connection page was visually inspected after correcting
text wrapping. Remaining desktop checks are paused while the user is using
the game. No editor visibility or MCP toggle success is inferred from status.

The implementation CI run passed all four Windows/Linux Python 3.11/3.12 jobs:
https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39097207057

The user-supplied 42.20.4 archive was inspected for unsafe paths/links, extracted
into separate staging and moved into place only after executable validation.
The previous game installation was retained as a separate backup. Normal saves,
mods and the existing isolated profile were outside the game-directory swap.
Native startup and the main menu confirm **42.20.4 b0bbce05d5**. The existing
profile's loaded world produced an actual heartbeat with `ready=true`,
`debug=true`, `single_player=true`, `player_loaded=true`, `god_mode=true`,
`operations_available=true` and `lua_execution_available=false`. This verifies
connection and actual startup god-mode state on the target build. MCP toggles
and visibly opened editors are recorded as they complete.

The final local suite passed **187 tests**, including 29 Windows GUI tests.
A fresh independent source review found no remaining required defects. Tests
cover compiler-free predefined operations and strict frames/auth/expiry/replay,
custom-Lua capability gating and GUI text-wrap recovery.


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
Remote Desktop Commander downloaded the published v0.4.0 ZIP onto APeX-2,
verified ZIP and executable SHA-256 digests, installed it per user and updated
the existing Start-menu target. Saved configuration and bridge-token hashes
are unchanged. The helper was updated inside the already-owned profile, with
startup god-mode and actual debug-status code present. The original DEBUG
shortcut still targets the game with `-debug`.

The installed `pz.exe` exposes all 11 default tools. A real installed stdio MCP
initialize/list/call exchange passed, including `debug_editors` invocation.
Codex's enabled global `project-zomboid` server points to that installed binary
with `serve`; a client refresh may be needed to discover it in existing chats.
Installed `bridge_status` correctly reports `ready=false` with no world loaded.
The installed GUI was not opened or visually inspected after the desktop stop.

Release assets match these SHA-256 values:

| Asset | SHA-256 |
| --- | --- |
| pz-windows.zip | `A2490C600CA715971DCC53F9AE0BC9A7F92CDC36DF8C418E38F573904626A2B6` |
| PZToolkit.exe | `8459C7557311615AB507C0AA443CF72C0B0FC19942FD34DB05BDECE35555EF7C` |
| pz.exe | `DC36119617F84DD6184784FD6F91E68B7F51DF8A095355FF55A0F2C548DF8A46` |
No source or fixture success establishes a connected world.

The [v0.4.0 CI run](https://github.com/raiinman/project-zomboid-toolkit/actions/runs/39096279934)
passed all four Windows/Linux Python 3.11/3.12 jobs for implementation commit
`6fc5ba41fbc0523e72a813ac55223318c001d275`. Windows 3.11 rebuilt and verified
both executables, including actual MCP protocol and native fixture GUI checks.
The released assets were also independently verified on the actual PC.

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
