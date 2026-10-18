"""Offline contracts using disposable game trees, never an installed game."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from pztoolkit.core import Toolkit


@pytest.fixture
def sandbox(tmp_path):
    game = tmp_path / "game"
    lua = game / "media" / "lua" / "shared"
    lua.mkdir(parents=True)
    (lua / "Fixture.lua").write_text("-- fixture\nfunction Fixture()\n    return 42\nend\n", encoding="utf-8")
    config = tmp_path / "pztoolkit.json"
    config.write_text(json.dumps({
        "game_dir": "game", "profile_dir": "profile", "workspace_dir": "workspace",
    }), encoding="utf-8")
    return Toolkit(config), config, tmp_path


def scaffold(toolkit, root, name="ExampleMod"):
    toolkit.mod_create(name)
    candidates = list((root / "workspace").rglob("mod.info"))
    return next(path.parent for path in candidates if f"id={name}" in path.read_text(encoding="utf-8").replace(" ", ""))


def cli(config, *arguments):
    return subprocess.run(
        [sys.executable, "-m", "pztoolkit", "--config", str(config), *arguments],
        text=True, capture_output=True, timeout=30, check=False,
    )


def directory_link(link, target):
    """Use Windows junctions because Path.is_symlink does not recognize them."""
    if sys.platform == "win32":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(target, target_is_directory=True)


def test_config_relative_paths_create_mod_inside_workspace(sandbox):
    toolkit, _, root = sandbox
    mod = scaffold(toolkit, root)
    assert mod.is_relative_to(root / "workspace")
    assert list(mod.rglob("*.lua")), "A new mod must contain a runnable Lua example"
    assert not (root / "game" / "mods").exists()


@pytest.mark.parametrize("profile,workspace", [("game/profile", "workspace"), ("profile", "profile/workspace"), ("profile", "profile")])
def test_overlapping_roots_are_rejected_before_profile_writes(tmp_path, profile, workspace):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"game_dir": "game", "profile_dir": profile, "workspace_dir": workspace}), encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        Toolkit(config).profile_prepare()
    assert not list(tmp_path.rglob(".pztoolkit-profile"))


@pytest.mark.parametrize("name", ["../escape", "a/b", "a\\b", "", ".", "..", "bad\nname", "bad=id"])
def test_mod_create_rejects_names_that_are_not_mod_ids(sandbox, name):
    toolkit, _, root = sandbox
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.mod_create(name)
    assert not (root / "escape").exists()


def test_source_read_is_confined_to_game_media(sandbox):
    toolkit, _, root = sandbox
    secret = root / "secret.txt"
    secret.write_text("private fixture", encoding="utf-8")
    for path in (str(secret), "../../secret.txt", "../secret.txt"):
        with pytest.raises((ValueError, RuntimeError)):
            toolkit.source_read(path)


def test_source_tools_refuse_linked_media_root(sandbox):
    toolkit, _, root = sandbox
    media = root / "game" / "media"
    outside = root / "outside-media"
    media.rename(outside)
    directory_link(media, outside)
    with pytest.raises(ValueError):
        toolkit.source_read("lua/shared/Fixture.lua")
    with pytest.raises(ValueError):
        toolkit.source_search("Fixture")
    assert (outside / "lua" / "shared" / "Fixture.lua").read_text(encoding="utf-8").startswith("-- fixture")


def test_source_search_and_read_return_only_requested_evidence(sandbox):
    toolkit, _, _ = sandbox
    found = toolkit.source_search("Fixture", limit=1)
    assert "Fixture" in json.dumps(found)
    source = toolkit.source_read("lua/shared/Fixture.lua", start=2, lines=1)
    assert "function Fixture()" in json.dumps(source)
    assert "return 42" not in json.dumps(source)


def test_mod_check_and_deploy_reject_outside_workspace(sandbox):
    toolkit, _, root = sandbox
    outside = root / "outside"
    outside.mkdir()
    (outside / "mod.info").write_text("name=Outside\nid=Outside\n", encoding="utf-8")
    for operation in (toolkit.mod_check, toolkit.mod_deploy):
        with pytest.raises((ValueError, RuntimeError)):
            operation(str(outside))


def test_deploy_rejects_traversal_in_mod_metadata(sandbox):
    toolkit, _, root = sandbox
    mod = scaffold(toolkit, root)
    info = mod / "mod.info"
    info.write_text(info.read_text(encoding="utf-8").replace("id=ExampleMod", "id=../../escape"), encoding="utf-8")
    assert toolkit.mod_check("mods/ExampleMod")["ok"] is False
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.mod_deploy("mods/ExampleMod")
    assert not (root / "escape").exists()


def test_harness_rejects_scenarios_outside_workspace(sandbox):
    toolkit, _, root = sandbox
    ready_bridge(toolkit, root)
    outside = root / "outside.lua"
    outside.write_text("return true", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.harness_run(str(outside), timeout=0.1)
    assert not (root / "profile" / "Lua" / "pzt-request.txt").exists()


def test_mod_create_refuses_overwrite_and_preserves_existing_work(sandbox):
    toolkit, _, root = sandbox
    mod = scaffold(toolkit, root)
    sentinel = mod / "keep.txt"
    sentinel.write_text("original work", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.mod_create("ExampleMod")
    assert sentinel.read_text(encoding="utf-8") == "original work"


def test_profile_prepare_refuses_existing_unowned_profile(sandbox):
    toolkit, _, root = sandbox
    profile = root / "profile"
    profile.mkdir()
    sentinel = profile / "personal-save.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.profile_prepare()
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not (profile / ".pztoolkit-profile").exists()


def test_game_launch_refuses_running_tracked_process_without_windows_signals(sandbox, monkeypatch):
    toolkit, _, root = sandbox
    toolkit.profile_prepare()
    (root / "game" / "ProjectZomboid64.exe").touch()
    (root / "profile" / "pzt-game.pid").write_text(str(os.getpid()), encoding="utf-8")
    if sys.platform == "win32":
        def forbidden_signal(*args):
            raise AssertionError("Windows os.kill(pid, 0) sends CTRL_C_EVENT")
        monkeypatch.setattr(os, "kill", forbidden_signal)
        def tasklist(command, **kwargs):
            assert command[0].lower() == "tasklist"
            assert f"PID eq {os.getpid()}" in command
            return subprocess.CompletedProcess(command, 0, f'"ProjectZomboid64.exe","{os.getpid()}","Console","1","1 K"\n', "")
        monkeypatch.setattr(subprocess, "run", tasklist)
    with pytest.raises(ValueError, match="already running"):
        toolkit.game_launch()


def test_game_launch_passes_isolated_profile_debug_and_mod_discovery_arguments(sandbox, monkeypatch):
    toolkit, _, root = sandbox
    toolkit.profile_prepare()
    executable = root / "game" / "ProjectZomboid64.exe"
    executable.touch()
    launches = []

    def launch(arguments, **options):
        launches.append((arguments, options))
        return SimpleNamespace(pid=424242)

    monkeypatch.setattr(subprocess, "Popen", launch)
    result = toolkit.game_launch()
    assert result["pid"] == 424242
    assert len(launches) == 1
    arguments, options = launches[0]
    assert arguments[0] == str(executable)
    assert "-debug" in arguments
    assert f"-cachedir={root / 'profile'}" in arguments
    assert arguments[arguments.index("-modfolders") + 1] == "mods"
    assert options["cwd"] == root / "game"
    assert (root / "profile" / "pzt-game.pid").read_text(encoding="utf-8") == "424242"


def test_deploy_refuses_unowned_collision_and_preserves_sibling_mod(sandbox):
    toolkit, _, root = sandbox
    scaffold(toolkit, root)
    toolkit.profile_prepare()
    collision = root / "profile" / "mods" / "ExampleMod"
    collision.mkdir(parents=True)
    sentinel = collision / "personal.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    sibling = collision.parent / "OtherMod"
    sibling.mkdir()
    (sibling / "personal.txt").write_text("also preserve", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.mod_deploy("mods/ExampleMod")
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert (sibling / "personal.txt").read_text(encoding="utf-8") == "also preserve"


def test_deploy_refuses_internal_junction_and_preserves_its_target(sandbox):
    toolkit, _, root = sandbox
    scaffold(toolkit, root, name="Foo")
    toolkit.profile_prepare()
    mods = root / "profile" / "mods"
    other = mods / "Bar"
    (other / "42").mkdir(parents=True)
    original = "name=Bar\nid=Bar\n"
    (other / "42" / "mod.info").write_text(original, encoding="utf-8")
    (other / ".pztoolkit-owned").write_text("pztoolkit-v1", encoding="utf-8")
    alias = mods / "Foo"
    directory_link(alias, other)
    with pytest.raises(ValueError):
        toolkit.mod_deploy("mods/Foo")
    assert (other / "42" / "mod.info").read_text(encoding="utf-8") == original
    assert alias.exists()
    assert alias.resolve() == other.resolve()


def test_owned_redeployment_updates_mod_and_preserves_siblings(sandbox):
    toolkit, _, root = sandbox
    mod = scaffold(toolkit, root)
    toolkit.profile_prepare()
    toolkit.mod_deploy("mods/ExampleMod")
    destination = root / "profile" / "mods" / "ExampleMod"
    assert (destination / ".pztoolkit-owned").read_text(encoding="utf-8").strip() == "pztoolkit-v1"
    sibling = destination.parent / "OtherMod"
    sibling.mkdir()
    (sibling / "personal.txt").write_text("preserve", encoding="utf-8")
    (mod / "changed.txt").write_text("second revision", encoding="utf-8")
    toolkit.mod_deploy("mods/ExampleMod")
    assert (destination / "42" / "changed.txt").read_text(encoding="utf-8") == "second revision"
    assert (sibling / "personal.txt").read_text(encoding="utf-8") == "preserve"


def ready_bridge(toolkit, root):
    toolkit.profile_prepare()
    lua = root / "profile" / "Lua"
    lua.mkdir(exist_ok=True)
    (lua / "pzt-status.txt").write_text(json.dumps({"ready": True, "timestamp_ms": int(time.time() * 1000), "build": "fixture"}), encoding="utf-8")
    return lua


def test_harness_rejects_stale_bridge_status(sandbox):
    toolkit, _, root = sandbox
    scaffold(toolkit, root)
    lua = ready_bridge(toolkit, root)
    (lua / "pzt-status.txt").write_text(json.dumps({"ready": True, "timestamp_ms": 1}), encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        toolkit.harness_run("scenarios/ExampleMod_smoke.lua", timeout=0.1)
    assert not (lua / "pzt-request.txt").exists()


def test_harness_timeout_never_accepts_stale_success_response(sandbox):
    toolkit, _, root = sandbox
    scaffold(toolkit, root)
    lua = ready_bridge(toolkit, root)
    (lua / "pzt-response.txt").write_text(json.dumps({"id": "0" * 32, "ok": True, "message": "old run"}), encoding="utf-8")
    result = toolkit.harness_run("scenarios/ExampleMod_smoke.lua", timeout=0.1)
    assert result["status"] == "timed_out"
    assert result["ok"] is False
    assert result["id"] != "0" * 32
    assert Path(result["report"]).is_file()
    assert json.loads(Path(result["report"]).read_text(encoding="utf-8"))["status"] == "timed_out"
    assert (lua / "pzt-request.txt").read_text(encoding="utf-8") == ""
    assert not (lua / "pzt-run.lock").exists()


@pytest.mark.parametrize("ok,status", [(False, "failed"), (True, "passed"), ("true", "invalid_response")])
def test_harness_preserves_correlated_scenario_result(sandbox, ok, status):
    """A fake game only tests transport and evidence, never live Lua behavior."""
    toolkit, _, root = sandbox
    scaffold(toolkit, root)
    lua = ready_bridge(toolkit, root)
    failures = []

    def simulated_game():
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            request = lua / "pzt-request.txt"
            if request.exists():
                lines = request.read_text(encoding="utf-8").splitlines()
                if len(lines) >= 4:
                    (lua / "pzt-response.txt").write_text(json.dumps({"id": lines[1], "ok": ok, "message": "fixture result"}), encoding="utf-8")
                    return
            time.sleep(0.01)
        failures.append("harness did not write a complete request")

    worker = threading.Thread(target=simulated_game, daemon=True)
    worker.start()
    try:
        result = toolkit.harness_run("scenarios/ExampleMod_smoke.lua", timeout=2)
    finally:
        worker.join(timeout=4)
    assert not failures
    assert result["status"] == status
    assert result["ok"] is (ok is True)
    assert result["message"] == ("Malformed matching bridge response" if status == "invalid_response" else "fixture result")
    assert Path(result["report"]).is_file()
    assert json.loads(Path(result["report"]).read_text(encoding="utf-8"))["id"] == result["id"]


@pytest.mark.parametrize("new_log,truncated", [("new session\n" + "new output\n" * 50, False), ("new session\n" + "new output\n" * 30000, True)], ids=["regrown", "regrown-over-capture-limit"])
def test_harness_detects_truncated_then_regrown_logs_and_reports_capture_limit(sandbox, new_log, truncated):
    toolkit, _, root = sandbox
    scaffold(toolkit, root)
    lua = ready_bridge(toolkit, root)
    log = root / "profile" / "console.txt"
    log.write_text("old session\nold output\n", encoding="utf-8")
    failures = []

    def simulated_game():
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            request = lua / "pzt-request.txt"
            if request.exists():
                lines = request.read_text(encoding="utf-8").splitlines()
                if len(lines) >= 4:
                    log.write_bytes(new_log.encode("utf-8"))
                    (lua / "pzt-response.txt").write_text(json.dumps({"id": lines[1], "ok": True, "message": "fixture result"}), encoding="utf-8")
                    return
            time.sleep(0.01)
        failures.append("harness did not write a complete request")

    worker = threading.Thread(target=simulated_game, daemon=True)
    worker.start()
    try:
        result = toolkit.harness_run("scenarios/ExampleMod_smoke.lua", timeout=2)
    finally:
        worker.join(timeout=4)
    assert not failures
    assert result["status"] == "passed"
    assert result["game_build"] == "fixture"
    assert result["execution_contract"] == "synchronous Lua assertions"
    assert result["log_rollover_detected"] is True
    assert result["logs_truncated"] is truncated
    expected = new_log.encode("utf-8")[:256 * 1024].decode("utf-8").splitlines()
    assert result["logs"] == expected
    assert result["logs"][0] == "new session"


def test_cli_lists_same_tools_as_shared_registry(sandbox):
    toolkit, config, _ = sandbox
    result = cli(config, "tools")
    assert result.returncode == 0, result.stderr
    listing = json.loads(result.stdout)
    entries = listing["tools"] if isinstance(listing, dict) else listing
    assert {entry["name"] for entry in entries} == set(toolkit.tools())


def test_cli_rejects_invalid_arguments_before_side_effects(sandbox):
    _, config, root = sandbox
    for args in ({"name": 123}, {"name": "Wrong", "unexpected": True}):
        result = cli(config, "call", "mod_create", "--args", json.dumps(args))
        assert result.returncode != 0
    assert not list((root / "workspace").rglob("mod.info"))


def test_cli_args_file_scaffolds_from_utf8_bom_json(sandbox):
    _, config, root = sandbox
    arguments = root / "arguments-é.json"
    arguments.write_text(json.dumps({"name": "FromFile"}), encoding="utf-8-sig")
    result = cli(config, "call", "mod_create", "--args-file", str(arguments))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["id"] == "FromFile"
    assert (root / "workspace" / "mods" / "FromFile" / "42" / "mod.info").is_file()


@pytest.mark.parametrize("arguments", [{"name": 123}, {"name": "Wrong", "unexpected": True}])
def test_cli_args_file_preserves_shared_strict_validation(sandbox, arguments):
    _, config, root = sandbox
    path = root / "arguments.json"
    path.write_text(json.dumps(arguments), encoding="utf-8")
    result = cli(config, "call", "mod_create", "--args-file", str(path))
    assert result.returncode != 0
    assert not list((root / "workspace").rglob("mod.info"))


def test_mcp_stdio_and_cli_expose_same_tools_schemas_and_results(sandbox):
    """Real MCP protocol traffic, not direct calls into the adapter."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    _, config, _ = sandbox
    listed = cli(config, "tools")
    assert listed.returncode == 0, listed.stderr
    payload = json.loads(listed.stdout)
    cli_tools = payload["tools"] if isinstance(payload, dict) else payload
    doctor = cli(config, "call", "doctor", "--args", "{}")
    assert doctor.returncode == 0, doctor.stderr

    async def check():
        params = StdioServerParameters(command=sys.executable, args=["-m", "pztoolkit", "--config", str(config), "serve"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                remote = await session.list_tools()
                assert {tool.name for tool in remote.tools} == {tool["name"] for tool in cli_tools}
                for tool in remote.tools:
                    local = next(item for item in cli_tools if item["name"] == tool.name)
                    assert tool.inputSchema == local["inputSchema"]
                result = await session.call_tool("doctor", {})
                assert not result.isError
                text = next(content.text for content in result.content if content.type == "text")
                assert json.loads(text) == json.loads(doctor.stdout)
                invalid = await session.call_tool("mod_create", {"name": 123})
                assert invalid.isError
                extra = await session.call_tool("mod_create", {"name": "Wrong", "unexpected": True})
                assert extra.isError

    asyncio.run(asyncio.wait_for(check(), timeout=30))
