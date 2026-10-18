# Project Zomboid Toolkit

<!-- impeccable:product-schema 1 -->

## Platform

Windows desktop, native Tk. CLI and stdio MCP remain separate adapters.

## Users and Purpose

The user and Codex already develop a mod directly. They want a Project Zomboid
game/debug/editor bridge similar in purpose to UEFN Toolbelt, through a desktop
app, CLI and MCP. The game's own mod browser and Steam Workshop handle mod
management. Do not provide a mod manager or a folder/project setup workflow.
Automatically use the existing saved game connection and its small Lua helper.

## Capabilities and Constraints

- Connect to the existing game session and expose debug and built-in editors.
- Automatically use existing game settings; preserve the installed game, mods
  and saves. No new authoring workspace is required.
- Run trusted inline Lua commands without scenario or report files per command.
- Expose built-in vehicle/attachment/world-map editors, animation viewer and
  debug menu through shared game-side requests. UI visibility needs live evidence.
- Present bridge readiness, game logs and command results in the app.
- Launch isolated tests with debug enabled and activate god mode at character
  load/respawn through the authenticated single-player bridge. Report actual
  god-mode state, including activation failures; preserve later manual disable.
- Preserve existing installations, normal saves, mods, source contracts and
  asynchronous responsiveness. Live in-world assertions remain unverified.
- Deliver a windowed `PZToolkit.exe` alongside the console `pz.exe`.

## Brand Commitments

Dead Signal Interactive branding is required. Keep the existing approved
distressed logo PNG unchanged, including the studio name and recognizable shape.
The current direction is a decrepit industrial toolbelt with beginner-friendly
instructions, original generated workshop artwork and quiet readable controls.
The user explicitly rejected green.
No actual aliens, predators, zombies or other creature figures belong in the UI.

The user rejected both the mod-first workflow and an optional mod-manager page.
Start with Connect, actual connection feedback, debug/god mode and built-in
editor actions. No folder controls or personal-mod creation. Explain actions in
plain language. Launch alone never establishes connection; require fresh status.

The user selected building the working GUI directly. Apply the relevant guidance
from their 3d-and-web library within native Tk controls.

## Evidence

The direct game toolbelt has offline protocol, Lua-mock and native-widget
regression checks. These do not establish live game or rendered visual
acceptance. Desktop control was stopped by the user, so final visual review
remains pending. Current measured build, install and test results belong in
`docs/validation.md`. Editor requests do not prove the editor appeared.
