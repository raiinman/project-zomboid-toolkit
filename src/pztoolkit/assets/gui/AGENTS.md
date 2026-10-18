# Purpose

Bundle the Dead Signal Interactive desktop identity and required visual assets.

## Ownership

GUI PNG artwork, the studio icon, the bundled display font and its license.
`README.md` records provenance and `prompts.md` records generated-art instructions.

## Local Contracts

- Preserve the user's recognizable studio symbol and wordmark. Distressed logo
  surfaces are approved; changing its geometry or spelling is not.
- Environmental horror only. Do not add actual aliens, predators, zombies or
  creature silhouettes to application artwork.
- Keep artwork away from controls and preserve readable, literal state feedback.
- Retain the font's SIL OFL license and its source provenance.
- Include these assets in wheel and frozen GUI builds. Load fonts privately in
  the app process; do not install them into system font directories.

## Work Guidance

Follow root DESIGN.md for palette, typography, density and native affordances.
Use the image-generation skill for raster artwork edits; keep original source
assets outside published commits when they belong to the user's separate kit.

## Verification

Run native GUI regression tests and the frozen GUI smoke check. They must load
the real images and font. Asset/source checks do not establish live game testing.

## Child DOX Index

No child DOX files. This document also owns `fonts/`.
