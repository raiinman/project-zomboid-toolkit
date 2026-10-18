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

- The root owns project rules, packaging, README, licensing, and global workflow.
- Children own domain rules and index their direct children.
- Create a child at durable boundaries with distinct responsibilities or checks.
- Child section order: Purpose, Ownership, Local Contracts, Work Guidance,
  Verification, Child DOX Index. Leave guidance/checks empty until they exist.
- Keep operational rules concise; disclose specialized reference through links.

## Project Contract

- Build one shared callable tool registry consumed by CLI and MCP adapters.
- First release serves mod development. Preserve server administration and
  gameplay automation as later capabilities in `docs/design.md`.
- Installed game content is read-only. Deploy and launch against a dedicated
  toolkit profile, keeping the user's normal saves and mods outside write scope.
- Live game behavior requires captured game evidence. Report offline tests and
  real game verification separately. A timeout is not a passing scenario.
- Keep tokens, local game files, saves, logs, and machine configuration out of Git.
- Before implementing public SDK/library calls, use current Context7 docs.

## User Preferences

- Distribute a standalone windowed `PZToolkit.exe` for mod management and in-game tests. Preserve `pz.exe` as the CLI/MCP entry point; the desktop workflow must not require PowerShell or a Python installation.
- Brand the GUI as Dead Signal Interactive with the approved distressed logo.
  Preserve its existing PNG while using the charcoal, ivory and studio-red
  sidebar workbench in DESIGN.md. The user rejected green. Keep creatures out
  of the interface and preserve clear native controls and evidence boundaries.
- Provide an optional eight-step guide with arrows pointing to the next control.
  Navigation through the guide must never imply that an operation succeeded.
- Continue authorized implementation and routine maintenance autonomously.
- Subagents are authorized. Coordinate ownership before concurrent edits.
- Treat user input during work as steering while preserving the active goal.
- Keep progress concise, state outcomes and one next step, and use no em dashes.

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

The root also owns `.github/`, packaging, examples, and other unindexed paths.
`PRODUCT.md` owns confirmed product/brand requirements. `DESIGN.md` owns the
desktop visual contract; `docs/design.md` remains the architecture authority.
`.impeccable/` holds the user's code-first design workflow and desktop brief;
scratch work and local review captures are ignored by Git.
`packaging/` owns the frozen GUI and console entry points, Windows build command
and executable smoke tests. Bundle the required runtimes and bridge assets;
verify the desktop window, CLI and MCP before delivery. Keep binaries in ignored
`dist/`. The root owns native app packaging and ZIP delivery contracts.
`packaging/build.ps1 -OutputDirectory dist/<version>` can preserve an older
running executable while building a new version; the default remains `dist`.
