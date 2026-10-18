# Toolbelt delivery plan

The current product is a direct game/debug/editor connection for the user and
Codex. Mod management, folder setup and saved scenario creation are not onboarding.
The [architecture](design.md) owns contracts; [validation](validation.md) owns
measured test and runtime evidence.

## Delivery slices

| Slice | Required outcome | Verification |
| --- | --- | --- |
| Shared game tools | Same 11 normal tools in desktop, CLI and MCP; legacy 17-tool view explicit | Schema parity, invocation and strict input tests |
| Existing connection | Reuse saved configuration and existing isolated profile | Config/default-path checks, token preservation and backup fixtures |
| Helper and launch | Install bridge, launch real game in debug, never require mod creation | Containment, helper upgrade and launch argument tests |
| Direct game actions | Inline Lua, verified god-mode toggle and allowlisted debug editors | Mock transport, error/timeout and editor ID tests |
| Beginner GUI | Open on Offline tools; explain saved logs/settings/script search and the separate live connection path | Game-closed GUI behavior tests, readiness gating and distinct rendered evidence |
| Artwork | Retain approved logo, use original decrepit workshop art, no green or figures | Asset checks plus native rendered review |
| Windows delivery | Frozen app/CLI/MCP, per-user install, preserved settings and Start menu entry | Executable smoke checks and PC-side installation verification |
| Live acceptance | Actual bridge, startup god mode, Lua outcomes and visible editor windows | Captured debug single-player evidence with game version |

## Offline-first update acceptance

These requirements describe the update; completion belongs in validation evidence.

- Open on **Offline tools** with saved settings, logs and installed script search/read.
- Keep these actions available when the test game is closed or disconnected.
- Explain missing logs as normal saved-history absence, not a connection failure.
- Explain that live god mode/editors need a loaded, unpaused debug single-player
  world with the bridge enabled; a main menu is insufficient.
- Disable live buttons until readiness is checked, and recheck before dispatch.
- Keep Lua compiler support separate from readiness and predefined game commands.
- Build in clean CI, scan the exact bundle and ZIP, then install without desktop
  input or GUI/game/Codex restarts. Preserve the current working MCP registration
  for this GUI-only change and verify offline behavior through a hidden probe.
- Record source tests, frozen GUI coverage, actual-PC Defender/install evidence
  and any deferred visual review separately. Do not imply a rendered user-PC check.

## Current acceptance checklist

- [x] Shared registry and strict validation architecture already exists.
- [x] Older scaffold/deploy operations remain available for existing scripts.
- [x] Final 11-tool public surface passes the complete offline suite.
- [x] Offline inline transport creates no scenario or per-command report files.
- [x] The final GUI has no mod manager, folder wizard or scenario-file workflow.
- [x] Saved settings, token and existing isolated profile survive upgrade.
- [x] Startup debug/god mode are confirmed in a loaded native world.
- [x] Historical v0.4.1 executable probes passed before the Defender quarantine.
- [x] Clean v0.4.2 candidate passes provenance and actual-PC Defender gates; installed MCP initialize/list/call succeeds.
- [ ] v0.4.2 frozen GUI probe and rendered review are completed when desktop work is authorized.
- [ ] A trusted signing identity is provisioned and actual signatures verify.
- [ ] Final rendered default/minimum windows, help, errors and advanced controls are inspected.
- [x] Installed app and Start menu entry are verified on the actual PC.
- [ ] Editor/mod acceptance continues during Javelin development, deferred by user.

Unchecked items are intentional evidence boundaries, not claims of failure.
Source implementation or mocked transport alone cannot check off native GUI or
in-game acceptance. A physical stop of desktop automation leaves rendered work
pending until the user authorizes it again.

## Verification method

Run focused behavior checks, then the full suite and frozen executable probes.
Verify installed-PC files rather than assuming the build environment's AppData
paths are the user's PC paths. Preserve existing configuration, profile, tokens
and unrelated game data. Keep generated local screenshots, logs and game files
out of published commits. Perform DOX closeout before delivery.

For a live run, enable the helper in Mods, load and unpause a debug single-player
world, check fresh readiness and actual god mode, execute passing/failing inline
Lua, then inspect requested editor windows. Record timeouts as unknown outcomes.
Do not automatically retry calls that may already have changed the world.

## Continuing limits

- Build/hotfix differences require shipped-source and actual runtime checks.
- A paused game may stop heartbeat and command progress.
- Host timeout cannot cancel Lua already running on the game thread.
- Editor request success does not prove a visible editor window.
- Multiplayer and server contexts remain unsupported.
- Deferred callback assertions are outside synchronous request verdicts.

The historical research and wiki coverage ledgers remain applicable. Further
tools need their own bounds, error contracts and game acceptance criteria.
