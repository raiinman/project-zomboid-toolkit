---
name: Project Zomboid Toolkit
description: A clear game toolbelt in a derelict industrial workshop.
colors:
  amber: "#e5b26d"
  soot: "#141416"
  steel: "#262326"
  edge: "#414047"
  ivory: "#f3eee4"
  ash: "#c4bcb1"
  control: "#303035"
  field: "#1b1b1f"
  selected: "#733c32"
  status: "#242328"
typography:
  display:
    fontFamily: "Oxanium SemiBold, Segoe UI"
    fontSize: "24pt"
    fontWeight: 600
  rail-title:
    fontFamily: "Oxanium SemiBold, Segoe UI"
    fontSize: "17pt"
    fontWeight: 600
  title:
    fontFamily: "Oxanium SemiBold, Segoe UI"
    fontSize: "13pt"
    fontWeight: 600
  body:
    fontFamily: "Segoe UI"
    fontSize: "11pt"
  code:
    fontFamily: "Consolas"
    fontSize: "11pt"
spacing:
  field: "10px"
  control-x: "14px"
  control-y: "10px"
  page: "16px"
  shell-x: "24px"
  shell-y: "20px"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.soot}"
    padding: "10px 14px"
  button-secondary:
    backgroundColor: "{colors.control}"
    textColor: "{colors.ivory}"
    padding: "10px 14px"
  field:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ivory}"
    padding: "10px"
  navigation:
    backgroundColor: "{colors.steel}"
    textColor: "{colors.ash}"
    padding: "13px 14px"
  status:
    backgroundColor: "{colors.status}"
    textColor: "{colors.ivory}"
    padding: "12px"
---

# Design System: Project Zomboid Toolkit

## Overview

**Creative North Star: "The Derelict Workshop"**

A readable game toolbelt inside a derelict workshop. Worn industrial artwork and the approved distressed Dead Signal Interactive logo carry the atmosphere; instructions and native controls stay quiet, clear and intact. The user rejected green and creature imagery.

The app serves the existing game and the user's existing work. Its visual
hierarchy leads from a clear connection action to useful game tools. It does not
borrow the complexity of an editor or turn internal transport files into tasks.

**Key Characteristics:**
- Warm industrial decay in imagery
- Plain instructions before technical detail
- Native controls with explicit state

## Colors

Warm amber marks action and focus; soot and steel keep the image's decay from
competing with the interface. Ivory is the reading color and ash carries secondary
instructions. Muted rust identifies selection. Error and warning treatments
remain distinct from ordinary status.

**The Quiet Controls Rule.** Keep texture in imagery and solid surfaces behind live instructions and controls.

## Typography

Oxanium SemiBold gives short headings an industrial character, with Segoe UI as
the platform fallback. Segoe UI carries instructions and controls; Consolas is
reserved for code and technical output. The token sizes are native Tk points,
not browser pixels. Do not apply texture, all-caps styling or distortion to
instructional copy. Oxanium's required OFL notice stays bundled.

## Layout

The native window opens at 1280 by 960 and permits a minimum of 1100 by 860.
The fixed sidebar is 238 pixels wide, with 18-pixel internal padding. The main
shell uses 24-pixel horizontal and 20-pixel vertical padding; page padding is
16 pixels. Copy wraps with the available width. Notebook page selection is
presented through sidebar buttons rather than duplicate native tabs.

A contained 130-pixel workshop image is an atmosphere surface, not a control
background. Technical output and advanced code disclose deliberately. The exact
current pages and their tasks belong in the desktop surface brief.

## Elevation & Depth

Tonal surfaces and restrained borders establish depth. Native buttons supply
hover, focus, pressed and disabled feedback; there are no decorative shadows or
idle animation. Progress appears only while a real worker action is running.

**The Literal State Rule.** Show connection and god-mode claims only from actual tool results; decoration never stands in for evidence.

## Shapes

Use familiar rectangular Tk controls and native focus/selection behavior.
No invented radius scale is defined. Distress lives in the approved logo and
original artwork rather than in button silhouettes or text.

## Components

### Buttons

The next connection action is prominent. Secondary controls use dark surfaces;
keyboard focus uses the amber accent. Disabled and busy states prevent duplicate
submissions. Plain next-step instructions support the next action without proving that it
succeeded.

### Inputs

Dark code fields use ivory text and an amber insertion/focus indicator. Code is
monospaced. Trust is explicit before sending privileged inline Lua. No folder
wizard or saved-scenario editor belongs in normal connection flow.

### Navigation and disclosure

Sidebar selection is visible through tonal contrast and text. Details start closed and built-in editors precede the advanced Lua tab;
ordinary results remain readable without raw JSON.
Do not add a mod manager or an authoring tour to the navigation.

### Status

Show useful plain-language results, including a next action when not connected.
Warning and error feedback must not look like passing game evidence. Request
completion cannot certify that a game editor window appeared.

## Do's and Don'ts

### Do:
- Do preserve the approved distressed logo PNG exactly.
- Do describe the next useful game action in plain language.
- Do keep technical output collapsed and inline Lua in the advanced tab.

### Don't:
- Don't introduce green or creature figures.
- Don't distress instructions, field text or controls.
- Don't turn mod creation, folder selection or saved scenarios into connection prerequisites.
