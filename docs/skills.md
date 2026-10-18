# Skills and framework provenance

The user requested available skills and their [skill-library](https://github.com/raiinman/skill-library/tree/main).
Skill discovery selected workflows relevant to a Python CLI/MCP and game harness.
Unrelated cloud, finance, artwork, office, video, and web UI workflows do not apply
to this repository. Applying every unrelated skill would add conflicting scope.

## Source snapshots

| Source | Revision | Use |
| --- | --- | --- |
| [raiinman/skill-library](https://github.com/raiinman/skill-library) | `d6bbba316347b12ab9df3fa3602b53a6e9adebeb` | Read catalog and relevant coding-workflow skills from the user fork |
| [raiinman/dox](https://github.com/raiinman/dox) | `b88194c34ace1a2a3dc01831d36b8a65986a41f5` | Installed adapted root/child AGENTS.md contracts |

DOX is MIT licensed, copyright (c) 2026 Agent Zero. The complete notice is
preserved in [DOX-LICENSE](DOX-LICENSE). Its framework rails remain: read the
applicable chain, update contracts after meaningful changes, maintain child
indexes, and perform closeout. The upstream README presentation section was
adapted to this project's title, badges, copyable commands, and evidence status.
Decorative assets from the DOX repository are not installed.

## Workflow use and evidence

| Skill | Application in this repository |
| --- | --- |
| using-agent-skills | Selected relevant workflows from the user library and retained authorized continuation |
| writing-for-agents | Concise root and local contracts, scoped pointers and DOX child indexes |
| spec-driven-development | Capability map, MVP criteria, explicit roadmap and evidence boundaries in `design.md` |
| planning-and-task-breakdown | Dependency order, independent subagent scopes, verification checkpoints in `plan.md` |
| api-and-interface-design | One tool registry, boundary validation, common errors, explicit retry semantics |
| documentation-and-adrs | Accepted architecture decisions, tradeoffs, operating limits and provenance |
| source-driven-development | Current Context7/API docs, official release notes, and installed game sources informed four requested research passes and compatibility changes |
| incremental-implementation | Registry first, adapters and mod tooling next, harness after wire contract |
| test-driven-development | Behavior checks for validation, transport errors, filesystem boundaries, and adapters |
| security-and-hardening | Read-only game tree, profile containment, token/expiry/correlation checks, privileged local bridge model |
| code-review-and-quality | Independent correctness/security review and verification before final commit |
| code-simplification | Reviewed registry/adapters and harness for needless abstraction and excessive indirection; no refactor required merely for style |
| ci-cd-and-automation | Verification agent added frozen-lock offline CI on Windows/Linux and Python 3.11/3.12 |
| doubt-driven-development | Read and applied adversarial artifact/contract checks; reviewer had prior documentation context, so this is not a fully isolated fresh-context or cross-model review |

The relevant library sources are under
[`skills/coding-workflow`](https://github.com/raiinman/skill-library/tree/d6bbba316347b12ab9df3fa3602b53a6e9adebeb/skills/coding-workflow).
Review used the
[quality workflow](https://github.com/raiinman/skill-library/blob/d6bbba316347b12ab9df3fa3602b53a6e9adebeb/skills/coding-workflow/code-review-and-quality/SKILL.md),
[security workflow](https://github.com/raiinman/skill-library/blob/d6bbba316347b12ab9df3fa3602b53a6e9adebeb/skills/coding-workflow/security-and-hardening/SKILL.md),
[simplification workflow](https://github.com/raiinman/skill-library/blob/d6bbba316347b12ab9df3fa3602b53a6e9adebeb/skills/coding-workflow/code-simplification/SKILL.md), and
[doubt workflow](https://github.com/raiinman/skill-library/blob/d6bbba316347b12ab9df3fa3602b53a6e9adebeb/skills/coding-workflow/doubt-driven-development/SKILL.md).
Security/performance reference checklists were consulted where applicable; web
headers, cookies, database, and frontend checks have no runtime surface here.

Review included disposable Windows child-process and directory-junction probes.
Windows child outcomes were inconsistent and were not accepted as definitive
process-control proof. The platform review used the official
[Python process-signal contract](https://docs.python.org/3/library/os.html#os.kill);
on Windows, signal zero overlaps `CTRL_C_EVENT` and is not a POSIX existence probe.
A subprocess-only mutation inverted the path containment guard; the scaffold
test failed under that mutation and passed against the unchanged implementation.
No implementation file was edited for that experiment. No paid cross-model CLI
review was invoked.

The user subsequently requested four internet research passes. Their source
inventory and findings belong in [research](research.md), with official, community,
local, and runtime evidence distinguished. The Lua/lifecycle pass used Context7
for event and Lua API references, official Java API pages and release notes, and
read-only inspection of installed Lua. Research identified hotfix-dependent
compiler availability, pause-related heartbeat limits, synchronous-only verdicts,
and log truncation. Installed-game investigation also required `.txt` wire files
for JSON payloads because its writer allowlist rejects `.json`. These findings
update contracts and tests; they do not replace live game acceptance.

The table records selected workflows and their concrete responsibilities, not a
claim that every skill checklist or live acceptance check has already passed.
Verification outcomes belong in the actual test output and release handoff.
Source-based validation of game Lua and SDK protocols is distinct from real game
scenario execution. The latter remains unverified until captured in a live run.

No global skill installation is required: the user's library clone and existing
installed engineering skills provide the workflow sources. DOX installation is
project-local and does not replace the user's global configuration.
