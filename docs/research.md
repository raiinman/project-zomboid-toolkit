# Four research passes: Project Zomboid modding

Research checked October 17, 2026. These were four distinct investigations using
multiple targeted internet searches, followed by source comparison and a gap
review. Developer publications and official APIs take priority. Community
documentation and author repositories are labelled below. This is a coverage
record, not a claim that all modding information is known.

The current official site identifies 42.21 as stable. The local game artifact
inspected during this work identifies itself statically as 42.20. Runtime build
and capabilities must still be captured by the in-game heartbeat. Older guides
describe different builds and cannot establish current behavior by themselves.
[Official 42.21 release](https://projectzomboid.com/blog/news/2026/09/42-21-stable-released/)

## Pass 1: packaging, metadata, versions, and source authority

Search themes: Build 42/common folder structure, local mod discovery, numbered
version selection, mod.info metadata, migration guides, and current releases.

The developer describes choosing the newest compatible numbered subdirectory,
with `common` for shared assets and legacy B41 content remaining at the root.
Our `42/` scaffold is one supported starting shape, not a general implementation
of the game's version selector. [Developer architecture explanation, August
2024](https://projectzomboid.com/blog/news/2024/08/tidy-up-time/)

The official metadata API represents dependencies, incompatibilities,
before/after ordering, game-version limits, Workshop identity, packs and tiles.
Checking `name`, `id`, and folders cannot certify those relationships. The
toolkit deliberately restricts its generated IDs and `42/mod.info` layout;
legitimate existing mods can have other IDs/layouts.
[ChooseGameInfo.Mod](https://projectzomboid.com/modding/zombie/gameStates/ChooseGameInfo.Mod.html)

The official 42.13 migration announcement supplies registry and inventory API
documents. We verified that announcement, but attachment downloads returned HTTP
403 during the first pass. The later wiki pass recovered and read public archive copies, as recorded in [wiki-research.md](wiki-research.md). Registry, item, trait,
profession and body-location templates need a dedicated follow-up against
installed definitions before implementation.
[Official migration announcement, December 2025](https://theindiestone.com/forums/topic/88499-modding-migration-guide-4213/)

Direct PZWiki fetches were blocked. Indexed documentation was useful for discovery
but was corroborated locally or labelled community-backed. The installed example
mod/template uses a legacy root layout, illustrating why shipped examples also
need version qualification.

Game and third-party mod content stays outside this repository. Future export or
Workshop packaging must distinguish original toolkit outputs from material it
does not own. [Developer modding policy](https://projectzomboid.com/blog/modding-policy/)

## Pass 2: Lua contexts, lifecycle, compilation, reload, and logs

Search themes: Lua API scopes, boot/player/world events, custom require/reload,
debug tools, tick scheduling, file I/O and log rollover.

Runtime compilation was disabled in 42.20.4 and restored in 42.21. The bridge now
checks `type(loadstring) == 'function'` and includes availability and a reason in
its heartbeat. A version number alone is insufficient evidence of capability.
[Official restoration notes](https://projectzomboid.com/blog/news/2026/09/42-21-stable-released/)

Boot, player creation and world readiness are distinct. Community event docs
also distinguish paused from running ticks. The bridge requires a loaded,
unpaused local world and explicitly excludes both network client and server
contexts. Its top-level mod sentinel proves loading only.
[Community event definitions](https://github.com/demiurgequantified/pzeventdoc/blob/develop/docs/Events.md),
[official networking/file globals](https://projectzomboid.com/modding/zombie/Lua/LuaManager.GlobalObject.html)

Installed `client/Tests/RecipeTests.lua` distributes work over multiple ticks.
Our current `pcall` scenario contract covers synchronous assertions only. A
callback that fails after its scenario returned is not a correlated test verdict.
Async recipes, timed actions and gameplay need a future explicit completion
contract and tick state machine.

PZ exposes its own require/reload machinery and loaded-file state. We do not
promise that clearing ordinary Lua `package.loaded` safely reloads a mod, its
closures or its event listeners. Restart/load is the supported development loop.
[Official LuaManager API](https://projectzomboid.com/modding/zombie/Lua/LuaManager.html)

Client logs can be cleared and rewritten when they reach their configured size.
The harness now adds request-ID BEGIN/END markers, compares log prefixes to detect
common rollover cases, and flags capped captures. Console capture remains bounded
best-effort evidence; a correlated response is the scenario verdict.
[Official 42.4.0 technical notes](https://theindiestone.com/forums/topic/81341-4240-unstable-released/)

The 2024 debugger blog mixes implemented inspection tools with planned work.
Installed debugger files corroborate reload/step tools, not every promised future
editor feature. [Developer debugger announcement](https://projectzomboid.com/blog/news/2024/02/leapdoid/)

## Pass 3: launch, profiles, activation, transport, and reproducibility

Search themes: cachedir/debug/modfolders arguments, local and per-save activation,
file extension restrictions, paused worlds, debugger-driven tests and headless
versus real client execution. Internet findings were checked against installed
argument parsing, file APIs and mod-selection code.

The inspected 42.20 writer permits only `ini`, `cfg`, `txt` and `log`.
Our original `.json` heartbeat/response names would fail silently. Both now carry
JSON in `.txt` files. A mod author's reproduction identified this behavior; the
official 42.20.1 hotfix added JSON writing, so the restriction must not be
generalized to every 42.20 patch.
[Original reproduction](https://theindiestone.com/forums/topic/97743-4220-getfilewriter-silently-returns-null-for-non-allowlisted-extensions-mod-data-writes-fail-with-no-error-and-no-log/),
[official 42.20.1 correction](https://theindiestone.com/forums/topic/98369-build-42201-stable-hotfix-released/)

Installed parsing confirms `-debug`, `-cachedir=<path>`, and `-modfolders` followed
by a separate comma-separated value. The launcher now selects `mods` only to
reduce duplicate installed/Workshop copies. Installed UTF-8 reader/writer code
resolves these files beneath `<cachedir>/Lua`. These are static source checks;
real client acceptance remains separate.
[Official file API](https://projectzomboid.com/modding/zombie/Lua/LuaManager.GlobalObject.html),
[developer-forum cachedir guidance](https://theindiestone.com/forums/topic/70193-game-does-not-start-at-all/)

The installed first-release reset clears the default active list if its release
sentinel is absent. Preparing a fresh profile does not guarantee activation.
Instructions therefore require confirming both bridge and mod in the Mods UI,
then creating a new disposable world. Existing-save mod lists are separate.
Plain generated IDs are accepted by the inspected ActiveModsFile parser; this
does not settle all Workshop-qualified serialization advice found online.
[Official ActiveModsFile API](https://projectzomboid.com/modding/zombie/modding/ActiveModsFile.html)

The shipped `DebugScenarios.lua` suggests a future reproducible-world bootstrap.
It is not integrated in this release. A JVM headless flag does not establish a
headless OpenGL client test runner. Pausing, debugger suspension, death and menu
transitions remain explicit live acceptance cases.

Runtime build and scenario SHA256 are captured in reports. Follow-up evidence
should include active mod IDs and hashes, world identity, sandbox fixture version,
bridge version, and client/server launch manifests. World fixtures need build
qualification; the developer explicitly warned about save transitions.
[Developer save compatibility warning](https://projectzomboid.com/blog/news/2026/07/next-steps-2/)

Read-only local evidence: `projectzomboid.jar`, SHA256
`E4661CA9CB168ABC995D3CF59994FA17F66BA8A4E2C2899CBFA48F7EACEA54B8`.
Its Core initializer constructs `GameVersion(42,20,"")`. No game code is bundled.

## Pass 4: content types, Java, multiplayer, and existing tools

Search themes: crafting/entities/items, assets and vehicles, maps/tiles/animation,
Java loaders, existing test frameworks, server identifiers and compatibility.

B42 includes richer crafting and server-authoritative inventory/TimedAction
behavior. A client Lua loading assertion cannot validate multiplayer correctness
or content semantics. Installed generated script trees include recipes, entities,
vehicles, weapons, items and physics. Later tooling needs templates and validators
for those types plus persistence, synchronization and reconnect tests.
[Official 42.20 feature overview](https://projectzomboid.com/blog/features-overview-build-42-20/)

Java modding has an existing runtime-agent ecosystem. The author's ZombieBuddy
guide describes versioned Java JAR packaging and loader metadata. Java tooling
must be an optional backend with exact game/JVM/loader compatibility checks.
It is incorrect to claim every Java mod requires replacing game class files.
[ZombieBuddy author repository](https://github.com/zed-0xff/ZombieBuddy),
[author modding guide](https://github.com/zed-0xff/ZombieBuddy/blob/master/doc/ModdingGuide.md)

ZBSpec already provides in-game Lua BDD tests with SP/client/server modes and
structured results. A future adapter or importer could reuse that ecosystem.
An author issue also documents Java patch persistence within a JVM, requiring
full restart for isolation. These are third-party project contracts, not official
PZ guarantees. [ZBSpec](https://github.com/zed-0xff/ZBSpec/blob/master/README.md),
[Java patch persistence](https://github.com/zed-0xff/ZombieBuddy/issues/13)

Vehicles combine script, Lua, model, texture, physics and passenger/part behavior.
Future asset tooling must check references and exercise visual/physics behavior.
Historical tutorial export settings were not accepted as verified B42 settings.
[Official VehicleScript API](https://projectzomboid.com/modding/zombie/scripting/objects/VehicleScript.html),
[official ModelScript API](https://projectzomboid.com/modding/zombie/scripting/objects/ModelScript.html)

The July 2026 launch announcement described mapping/animation tools as forthcoming.
This research did not establish their later release state. Verify distribution
and version before promising editor automation.
[Official B42.20 release](https://projectzomboid.com/blog/news/2026/07/project-zomboid-build-42-20-released/)

Workshop download IDs, contained Mod IDs and dependencies are separate identities.
Conflicting historical backslash advice and checksum-disable workarounds are not
a reliable configuration recipe. Future server tooling must use the installed
server parser and preserve verification settings.
[Official support-staff identifier guidance](https://theindiestone.com/forums/topic/45463-added-mods-not-working/)

## Result and remaining gaps

Research changed the implementation: allowed wire extensions, runtime compiler
checks, explicit single-player guards, restricted mod discovery, clearer
activation instructions, synchronous test semantics, bounded responses and log
rollover evidence. The generated scaffold is intentionally a narrow Lua starting
point.

Still unverified: actual client launch/activation and passing/failing live
assertions; pause/resume and debugger behavior; later patch compatibility;
later migration-guide changes beyond the pinned archive; async scenarios; general version-folder selection;
dependencies and semantic scripts; binary assets; Workshop packaging; Java agent
installation; multiplayer and deterministic world bootstrap. These are tracked
in the [design](design.md) and [delivery plan](plan.md), not hidden assumptions.
