# Project Zomboid Toolkit

<!-- impeccable:product-schema 1 -->

## Platform

Windows desktop, native Tk. CLI and stdio MCP remain separate adapters.

## Users and Purpose

The user develops Project Zomboid mods and wants to manage them and run in-game
tests from a proper app window, without PowerShell or a Python installation.
The same tools must remain available through CLI and MCP.

## Capabilities and Constraints

- Configure isolated game profiles and development workspaces.
- Create, check and deploy development mods; edit and run trusted Lua scenarios.
- Present bridge readiness, game logs and retained reports in the app.
- Preserve existing installations, normal saves, mods, source contracts and
  asynchronous responsiveness. Live in-world assertions remain unverified.
- Deliver a windowed `PZToolkit.exe` alongside the console `pz.exe`.

## Brand Commitments

Dead Signal Interactive branding is required. Keep the existing approved
distressed logo PNG unchanged, including the studio name and recognizable shape.
The current direction is a charcoal, ivory and studio-red workbench with sidebar
navigation and a resizable activity dock. The user explicitly rejected green.
No actual aliens, predators, zombies or other creature figures belong in the UI.

The user requested guidance for someone learning the app. Provide an optional
eight-step walkthrough, concise instructions and arrows pointing to relevant
actions. Advance automatically only after the corresponding successful operation;
require actual bridge readiness before advancing that step. Manual guide
navigation never establishes operational success.

The user selected building the working GUI directly. Apply the relevant guidance
from their 3d-and-web library within native Tk controls.

## Evidence

The new GUI exists and has native widget regression coverage, including guide
progression and readiness checks. All three pages have native default/minimum
layout inspection. Frozen GUI, CLI and MCP smoke checks passed. Complete rendered
coverage of busy, empty and edited-scenario states remains outstanding.
Current measured outcomes belong in docs/validation.md. The user's existing Dead
Signal brand kit supplies the original logo. A screenshot of a scenario result
does not establish game execution unless it came from the live bridge.
