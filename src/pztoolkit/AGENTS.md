# Purpose

Implement shared Project Zomboid development tools and their adapters.

## Ownership

This subtree owns Python tools, configuration, CLI/MCP presentation, harness
transport, and packaged Lua bridge assets.

## Local Contracts

- Define tools once in the registry. CLI and MCP expose the same names and input
  contracts and invoke the same implementation.
- Resolve and constrain filesystem paths before writes and source reads.
- Bridge execution is local, opt-in, authenticated, and confined to the isolated
  debug single-player profile; require both client and server networking flags
  to be false. Bound requests, responses, and waits; correlate response IDs.
- Use `.txt` for in-game wire files, including JSON status and response payloads.
  The inspected Build 42.20 file-writer allowlist rejects `.json` filenames.
- Check compiler capability at runtime; 42.20.4 removed dynamic compilation,
  while 42.21 restored it. Report unavailable compilation as a readiness reason.
- Harness success covers synchronous assertions only. Deferred callback failures
  require a future asynchronous completion protocol. OnTick heartbeat can become
  stale while a world is paused; make that limitation explicit in diagnostics.
- `mod_check` validates the toolkit's `42/` scaffold. Keep broader version-folder,
  dependency, Java, map, asset, and multiplayer validation in the roadmap until
  each capability has its own supported contract and verification.
- Write machine-readable scenario evidence and distinguish game failure, timeout,
  malformed response, and successful assertions.
- Keep MCP stdout reserved for protocol traffic.

## Work Guidance

Add small slices with tests for observable behavior. Keep adapters thin and use
the installed game's Lua files as the version-specific source of truth.

## Verification

Run the relevant tests under `tests/`. Only a real client run can validate Lua
API assumptions, launch flags, and mod activation for the installed game build.

## Child DOX Index

No child DOX files currently exist. This file owns the entire package subtree.
