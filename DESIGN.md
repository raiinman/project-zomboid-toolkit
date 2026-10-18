# Dead Signal studio workbench

The user requested a new GUI using their 3d-and-web skill library, explicitly
rejected green, and required keeping the existing distressed studio logo. The
new layout is a native studio workbench, with sidebar navigation and a resizable
activity dock. Product truth stays in PRODUCT.md;
tool architecture stays in docs/design.md.

## Direction contract

The app remains a recognizable native mod-development tool: Setup, Mods and
In-game tests pages; conventional buttons, forms, tables and an editor. The visual
world contributes type, palette, density and the retained distressed studio mark.
It never changes action names or invents fictional telemetry.

- Graphite `#141416`, raised charcoal `#1e1e22`, quiet dividers `#414047`, ivory
  `#f1edef`, muted platinum `#bcb5bc`, and studio red `#ef8b82`. No green in
  navigation, controls, progress, selection, focus or status surfaces.
- Actual Dead Signal Interactive logo, with user-approved scratched/grimed
  surfaces while preserving its DS shape and wordmark.
- Remove the panoramic facility image from the UI. Keep the distressed logo
  byte-for-byte, placed in the navigation rail. No creatures or fictional gauges.
- Bundled Oxanium SemiBold for short display headings. Segoe UI body copy and
  Consolas code preserve native readability and familiar data editing.
- Errors and unknown test outcomes keep literal recovery text and distinct
  colors. Never imply a test passed through decorative green lighting alone.
- No flicker, strobe, fake enemy counters, fake connectivity or intrusive motion.
  Progress animation runs only during an actual background tool call.

## Layout plan and review

Left alignment, a 238-pixel studio rail, workspace-specific page titles, clear
selection and a vertically resizable activity dock replace the banner-and-tabs
composition. Existing mod tables and scenario controls remain direct and familiar.

The initial plan risked being only a red recolor of the old horror console. The
revised plan removes the wide scenic header, changes navigation and work-area
structure, gives results a useful resize handle, and shows progress only while
work runs. This makes the new layout functionally different without changing
tool contracts. The library's frontend-design guidance governs hierarchy and
content; its motion guidance keeps animation tied to real work, not decoration.

## Guided workflow

An optional guide strip shows eight steps: Save setup, Prepare test profile,
Create mod, Check selected, Deploy to test profile, Launch test game, Check bridge,
and Run saved scenario. A real arrow highlights the matching button on the
current page. Show me opens that page; Previous and Next revisit instructions.
Hide the guide through Show guide in the sidebar.

Successful operations advance the corresponding step. Failed actions and a
not-ready bridge leave it in place. Manual guide navigation never changes tool
outcomes. Keep the arrow clear during background work and preserve normal mouse
and keyboard access to the highlighted control.

## Verification

Inspect the native 1280 x 960 default and 1100 x 860 minimum window sizes across
all three pages, including
focus, selection, busy, empty, error and edited-scenario states. Preserve the
existing GUI regression tests and frozen CLI/MCP smoke checks. Windows-native
Tk is outside the HTML/CSS detector's scope. A fresh finish review uses captures
of the actual app, not a generated mockup. Live game assertions remain a separate
acceptance gate.
