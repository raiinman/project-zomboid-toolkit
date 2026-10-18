# DOX framework

DOX is installed as the AGENTS.md hierarchy for this repository. Derived from
`raiinman/dox` at `b88194c34ace1a2a3dc01831d36b8a65986a41f5` under MIT;
see `docs/DOX-LICENSE` and `docs/skills.md` for provenance.

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees.
- Source, instructions, records, assets, and durable docs must be understandable
  from the nearest AGENTS.md plus its parents.

## Read Before Editing

1. Read this root and identify every target path.
2. Walk from the root to each target and read every applicable AGENTS.md,
   including indexed children whose scopes contain the target.
3. Use the nearest doc for local work and parent docs for repository rules.
4. Closer docs control local details, but may not weaken DOX.

Re-read the applicable chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass. Update the closest owning doc when
purpose, structure, contracts, inputs, outputs, permissions, side effects,
workflow, quality standards, user preferences, or child indexes change. Update
affected parents and children and remove stale or contradictory text. Small
edits that preserve contracts may leave docs unchanged after this pass.

## Hierarchy

- The root owns project rules, release policy, README, licensing and global workflow.
- Children own domain rules and index their direct children.
- Create a child at durable boundaries with distinct responsibilities or checks.
- Child section order: Purpose, Ownership, Local Contracts, Work Guidance,
  Verification, Child DOX Index. Leave guidance/checks empty until they exist.
- Keep operational rules concise; disclose specialized reference through links.

## Project Contract

- Build one shared callable tool registry consumed by CLI and MCP adapters.
- Serve a direct game/debug/editor toolbelt for Codex and the user's existing
  mods. Do not build a mod manager, authoring page or folder-setup workflow.
  Steam Workshop and the game's own mod browser own mod management.
  Preserve later capabilities in `docs/design.md` without claiming them built.
- Installed game content is read-only. Deploy and launch against a dedicated
  toolkit profile, keeping the user's normal saves and mods outside write scope.
- Built-in god mode and editor operations must work without dynamic Lua
  compilation on 42.20.4. Inline Lua availability is a separate capability.
- Live game behavior requires captured game evidence. Report offline tests and
  real game verification separately. A timeout is not a passing scenario.
- Keep tokens, local game files, saves, logs, and machine configuration out of Git.
- Before implementing public SDK/library calls, use current Context7 docs.
- Build Windows candidates in clean CI, reject unexpected native dependency
  origins and scan the exact bundle before executable verification or delivery.
  Never restore quarantined builds, add antivirus exclusions or assert a false
  positive without evidence. Trusted signing requires a validated signing
  identity; unsigned candidates must remain explicitly labeled.

## User Preferences

- Distribute a standalone windowed `PZToolkit.exe` for game debugging and in-game tests. Preserve `pz.exe` as the CLI/MCP entry point; the desktop workflow must not require PowerShell or a Python installation.
- Install the Windows app per user with a Start menu entry under Dead Signal
  Interactive. Preserve existing configuration, workspaces and isolated profiles.
- Brand the GUI as Dead Signal Interactive with the approved distressed logo.
  Preserve its existing PNG while using the charcoal, ivory and studio-red
  sidebar workbench in DESIGN.md. The user rejected green. Keep creatures out
  of the interface and preserve clear native controls and evidence boundaries.
- Explain actions in beginner language and keep technical output behind Details.
  Automatically use the existing saved game connection. Do not expose folder
  choices or require new project/workspace/scenario files. Inline commands use
  the fixed bridge transport, not a saved script or report per command.
- Default GUI, CLI and MCP expose the same game/debug/editor toolbelt. Legacy
  file/scaffold tools remain accessible only with explicit CLI --all-tools.
- Use image-generated decrepit industrial artwork while keeping controls
  readable. Preserve the approved logo and no-green/no-creatures rules.
- Label the game launcher "Launch Project Zomboid (test profile)" in the GUI,
  guide and operating instructions so the real game's isolated profile is clear.
- Start isolated test sessions with debug enabled and god mode enabled when each
  character loads or respawns. Keep this confined to the authenticated local
  single-player bridge and report the actual god-mode state in bridge readiness.
- Reuse saved connection settings. If absent, detect the game internally and
  initialize only the app-owned connection defaults, without a folder wizard.
- Continue authorized implementation and routine maintenance autonomously.
- Subagents are authorized. Coordinate ownership before concurrent edits.
- Treat user input during work as steering while preserving the active goal.
- Keep progress concise, state outcomes and one next step, and use no em dashes.
- Editor visibility and mod integration testing continue during Javelin work.
  Do not require a separate editor/mod acceptance pass for the current cursor
  and god-mode fix, and do not label deferred checks as passed.

## README Presentation

Keep a centered project title, compact status badges, and verified local document
shortcuts. Keep examples copyable, status claims evidence-based, and attribution
visible. Decorative artwork is optional; its presence never implies validation.

## Closeout

1. Re-check changed paths against their DOX chains.
2. Update owning docs and affected parents, children, and child indexes.
3. Remove stale contracts and run relevant existing verification.
4. Report unverified behavior and docs intentionally left unchanged with reasons.

## Child DOX Index

| Child | Scope |
| --- | --- |
| `src/pztoolkit/AGENTS.md` | Shared tools, desktop/CLI/MCP adapters, harness, bundled assets |
| `tests/AGENTS.md` | Offline verification and integration test evidence |
| `docs/AGENTS.md` | Design, plan, provenance, operating instructions |
| `packaging/AGENTS.md` | Windows builds, provenance, signing and scan gates |

The root also owns `.github/`, examples and other unindexed paths.
`PRODUCT.md` owns confirmed product/brand requirements. `DESIGN.md` owns the
desktop visual contract; `docs/design.md` remains the architecture authority.
`.impeccable/` holds the user's code-first design workflow and desktop brief;
scratch work and local review captures are ignored by Git.
`packaging/AGENTS.md` owns build, provenance, signing, scan and executable-probe
contracts. Keep binaries and machine-specific receipts in ignored `dist/`.
The root owns release policy and installation evidence boundaries.
`packaging/build.ps1 -OutputDirectory dist/<version>` can preserve an older
running executable while building a new version; the default remains `dist`.
