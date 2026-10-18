# PZWiki: four passes and coverage ledger

Checked October 17, 2026, following the user's request to review
[the Modding website](https://pzwiki.net/wiki/Modding) in four passes.

The English Modding hub and its expanded navigation exposed **173 internal URL
entries**. Every entry is accounted for in [wiki-coverage.csv](wiki-coverage.csv):

| Depth | Hub URL entries |
| --- | ---: |
| Substantive article/overview reviewed | 139 |
| Index/overview inspected; descendants not exhaustively audited | 13 |
| Selected reference sections reviewed | 8 |
| Short/incomplete stub reviewed | 3 |
| Explicitly outside technical English review scope | 10 |

The ledger also includes **16 drill-down URLs**, for **189 rows** total. URL
counts include aliases that render the same article. The 10 exclusions are five
language variants, the game/Steam/Discord landing pages, a page-version template,
and an author profile. They were inventoried, not silently counted as read.

This is broad coverage of the linked modding site, **not a claim that every page
on PZWiki, every category descendant, API member, image, video, Discord discussion,
or external repository has been read or tested**. Large reference datasets have
explicit depth labels. Missing page-version values mean not observed, not current.
Article edit dates and version badges are separate evidence.
Some version badges are automatically updated and do not prove compatibility.
For category entries, the ledger's `index_reviewed` status means introduction and
navigation inspection; it does not claim that every category member was read.

Browser reads initially worked where the search fetcher was blocked. Ordinary
public HTML requests subsequently provided current article bodies, with requests
spaced one second apart per reader. Raw article snapshots remain in local scratch
storage; this repository contains original summaries and links, not a wiki mirror.

## Pass 1: site map, foundations, packaging, and official guides

The hub, getting-started guide, file formats, mod structure, metadata, community
resources and documentation indexes were reviewed. Categories were treated as
indexes, not proof their descendants were audited.

The getting-started guide ranks installed game behavior above generated docs and
wiki prose. Mod structure also warns about duplicate Mod IDs across discovery
locations and recommends Workshop packaging for publishing. This toolkit authors
outside game folders and deliberately stages copies into an isolated `mods`
profile with restricted discovery; it does not yet build Workshop uploads.
[Getting started](https://pzwiki.net/wiki/Getting_started_with_modding),
[mod structure](https://pzwiki.net/wiki/Mod_structure)

The structure article contains conflicting wording about whether `common` is
mandatory, while its versioning examples distinguish common assets from effective
versioned files. Our validator requires the toolkit's own conservative scaffold;
it is not a universal validator for all valid mod layouts. Case-sensitive paths,
effective-path collisions and version-folder selection need separate checks.
[Mod structure](https://pzwiki.net/wiki/Mod_structure),
[mod.info](https://pzwiki.net/wiki/Mod.info)

The wiki links a public archive of official guides, resolving the initial forum
attachment failure. The three-page registry migration guide and 18-page inventory
API guide were read, with representative rendered code/architecture pages checked.
The archive was pinned to `56568c01ef7f771663066e504aa2620b7a7e4be3`.
[TIS guide index](https://pzwiki.net/wiki/TIS_Modding_Guides),
[pinned public archive](https://github.com/pz-wiki-modding/Archive.Project-Zomboid-Modding/tree/56568c01ef7f771663066e504aa2620b7a7e4be3/TIS%20guides/B42%20unstable%20MP)

The migration guide requires the exact `media/registries.lua` phase before
ordinary Lua/scripts, registered identifiers, and updated item metadata. Future
item/trait templates must combine registration, script definitions, translations
and assets, rather than simply adding a shared Lua file. This is a 42.13 migration
contract to recheck against the target build.
[Migration guide mirror](https://github.com/pz-wiki-modding/Archive.Project-Zomboid-Modding/blob/56568c01ef7f771663066e504aa2620b7a7e4be3/TIS%20guides/B42%20unstable%20MP/Migration%20Guide.pdf)

The inventory guide separates client presentation from server mutation through
`perform` and `complete`; single-player executes both. Constructor values must
survive reconstruction, duration is server-derived, and changes need appropriate
synchronization. This is why later multiplayer tests must exercise both authority
and persistence, not merely observe a client-created item.
[Inventory API guide mirror](https://github.com/pz-wiki-modding/Archive.Project-Zomboid-Modding/blob/56568c01ef7f771663066e504aa2620b7a7e4be3/TIS%20guides/B42%20unstable%20MP/Project%20Zomboid_%20API%20for%20Inventory%20Items.pdf)

## Pass 2: Lua, events, state, dependencies, and Java

Lua/Kahlua, event pages, networking, registries, load order, UI, persistence,
documentation sources, editor helpers and library overviews were reviewed.

Folder placement is not an authorization boundary. The Lua API article describes
multiplayer clients loading server Lua too, while dedicated servers omit client
Lua. The bridge therefore explicitly requires both networking flags to be false.
The generic event guide's `OnCreatePlayer` example disagrees with its specific
event page, which documents `(playerNum, player)`. Overview examples need precise
API checks. [Lua API](https://pzwiki.net/wiki/Lua_(API)),
[event overview](https://pzwiki.net/wiki/Lua_event),
[OnCreatePlayer](https://pzwiki.net/wiki/OnCreatePlayer)

Persistence and network synchronization are distinct. Plain mod data should not
contain Java instances; online player IDs are temporary. UI tests also need
manager/listener cleanup and rendered behavior, not only object existence.
[Mod data](https://pzwiki.net/wiki/Mod_data),
[Networking](https://pzwiki.net/wiki/Networking),
[User Interface](https://pzwiki.net/wiki/User_Interface)

Custom event libraries add dependencies, not vanilla events. Old event stubs point
to Umbrella, while PZEventDoc also supplies wiki event data, so those two sources
are not independent corroboration. Older reflection overviews must be reconciled
with later restrictions. Java loaders such as Leaf require startup-time loading.
[Umbrella](https://pzwiki.net/wiki/Umbrella_(modding)),
[PZEventDoc](https://pzwiki.net/wiki/PZEventDoc),
[Leaf](https://pzwiki.net/wiki/Leaf),
[Starlit Library](https://pzwiki.net/wiki/Starlit_Library)

## Pass 3: debugging, harnesses, launch, projects, and publishing

Launch/debug pages, logs, multiplayer testing, troubleshooting, publishing and
related project descriptions were reviewed, with current pages replacing stale
indexed snapshots.

Startup documentation supports restricted mod discovery and separates launcher
diagnostics from game logs. Debugger suspension can explain an inconclusive
timeout. Existing-save activation, first-launch resets and role-specific log
files require real client checks. The multiplayer test guide still carries a
Build 41 badge and rewrite warning.
[Startup parameters](https://pzwiki.net/wiki/Startup_parameters),
[Lua debugger](https://pzwiki.net/wiki/Lua_debugger),
[Console](https://pzwiki.net/wiki/Console),
[multiplayer testing](https://pzwiki.net/wiki/Testing_mods_in_multiplayer)

Several superficially similar projects solve different problems. Pythoid is an
older embedded Jython integration, DOME is an object extractor, and the PZ AI agent
page establishes a demonstration rather than a reusable protocol. ZBundler overlaps
authoring/packaging workflows and merits future interoperability assessment.
[Pythoid](https://pzwiki.net/wiki/Pythoid),
[DOME](https://pzwiki.net/wiki/DOME),
[PZ AI agent](https://pzwiki.net/wiki/PZ_AI_agent),
[ZBundler](https://pzwiki.net/wiki/ZBundler)

Future publishing must preview content and metadata changes. Uploader operations
can overwrite descriptions, and deleted files may remain for subscribers.
Decompiler line remapping can modify the installed game, so it does not belong in
automatic read-only source inspection. PersistentOutfitID is unsuitable as a
durable entity key, and contradictory day-length examples reinforce using actual
sandbox settings. [Uploading mods](https://pzwiki.net/wiki/Uploading_mods),
[Zomboid Decompiler](https://pzwiki.net/wiki/Zomboid_Decompiler),
[PersistentOutfitID](https://pzwiki.net/wiki/PersistentOutfitID),
[Game time](https://pzwiki.net/wiki/Game_time)

## Pass 4: content scripts, assets, maps, localization, and tools

Content-type guides, scripts, rigs, maps, tiles, loot, localization, sound, radio
and their tool overviews were reviewed. Long parameter/ID datasets retain
selected-section labels in the ledger.

Translations changed to UTF-8 JSON in 42.15, while some hair/voice/flier tutorials
retain old `.txt` examples. Craft recipes, inputs, script TimedActions and Lua
timed-action classes are separate systems. Soft-override behavior is not uniformly
documented as tested. Future templates need resolved-engine reference checks.
[Translation](https://pzwiki.net/wiki/Translation),
[CraftRecipe](https://pzwiki.net/wiki/CraftRecipe),
[TimedAction scripts](https://pzwiki.net/wiki/TimedAction_(scripts))

Maps need exported-cell conflict detection, not merely load-order fixes. The
mapping overview distinguishes 300-cell authoring from B42's 256-cell exports.
Tile allocation lists are incomplete and mix versions. Loot chances are not
simple percentages; seeded/repeated generation tests are needed.
[Mapping](https://pzwiki.net/wiki/Mapping),
[tiledef allocations](https://pzwiki.net/wiki/Tiledefs_used_by_mods),
[procedural distributions](https://pzwiki.net/wiki/Procedural_distributions)

Retired/obsolete resources must not become defaults: ItemZed, TranslationZed, the
old B42 Map site and B41 vanilla map exports have explicit limitations. Clothing
and animation-tool pages include stubs; Texturing is a redlink. Attachment and
loot editors also have consequential mutation behaviors, to be scoped to
disposable fixtures. [ItemZed](https://pzwiki.net/wiki/ItemZed),
[TranslationZed](https://pzwiki.net/wiki/TranslationZed),
[B42 Map](https://pzwiki.net/wiki/B42_Map),
[Attachment Editor](https://pzwiki.net/wiki/Attachment_Editor),
[LootZed](https://pzwiki.net/wiki/LootZed)

## Decisions carried into the project

Retain the narrow local Lua milestone, explicit runtime capability checks,
read-only game source, isolated staging, synchronous verdicts and reproducible
evidence. General content validation, async tests, dependency resolution, Java,
binary assets, Workshop publishing and multiplayer each need their own fixtures
and acceptance criteria. The broader four internet passes are recorded separately
in [research.md](research.md); execution evidence is in [validation.md](validation.md).
