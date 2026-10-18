import json

import pytest

from pztoolkit.core import Toolkit


@pytest.fixture
def kit(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"game_dir": "game", "profile_dir": "profile", "workspace_dir": "projects"}))
    (tmp_path / "game/media/lua").mkdir(parents=True)
    return Toolkit(config)


def test_scaffold_has_build42_structure_and_smoke_test(kit):
    result = kit.mod_create("Example")
    assert result["mod"] == "mods/Example"
    assert kit.mod_check(result["mod"])["ok"]
    assert (kit.workspace / result["scenario"]).read_text().startswith("assert(")


def test_registry_rejects_invalid_inputs_before_dispatch(kit):
    with pytest.raises(ValueError, match="name"):
        kit.call("mod_create", {"name": 123})
    with pytest.raises(ValueError):
        kit.call("doctor", {"unexpected": True})


def test_roots_cannot_overlap(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text(json.dumps({"game_dir": "game", "profile_dir": "game/profile", "workspace_dir": "projects"}))
    with pytest.raises(ValueError, match="overlap"):
        Toolkit(config)


def test_launch_never_uses_kill_to_probe_a_windows_pid(kit, monkeypatch):
    import os
    import subprocess
    import pztoolkit.core as core

    if os.name != "nt":
        pytest.skip("Windows-specific process-probe regression")
    kit.profile_prepare()
    (kit.game / "ProjectZomboid64.exe").write_text("fixture")
    (kit.profile / "pzt-game.pid").write_text("12345")
    monkeypatch.setattr(os, "kill", lambda *args: pytest.fail("Windows kill probe must never run"))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, '"ProjectZomboid64.exe","12345","Console","1","10 K"\n', ""))
    monkeypatch.setattr(core.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Duplicate launch"))
    with pytest.raises(ValueError, match="already running"):
        kit.game_launch()


@pytest.mark.parametrize("unowned", [False, True])
def test_offline_tools_work_without_preparing_or_reading_unowned_profile(kit, unowned):
    if unowned:
        (kit.profile / "Lua").mkdir(parents=True)
        (kit.profile / "console.txt").write_text("private log")
        (kit.profile / "Lua/pzt-status.txt").write_text('{"ready": true}')
    source = kit.game / "media/lua/example.lua"
    source.write_text("-- offline source fixture")
    before = {p.relative_to(kit.profile).as_posix(): p.read_bytes()
              for p in kit.profile.rglob("*") if p.is_file()}
    assert kit.logs_read()["lines"] == []
    assert kit.logs_read()["reason"] == "profile_not_prepared"
    assert kit.bridge_status()["game_state"] == "unknown"
    assert kit.bridge_status()["reason"] == "profile_not_prepared"
    assert kit.source_search("offline")["matches"][0]["path"] == "lua/example.lua"
    assert kit.source_read("lua/example.lua")["lines"] == ["-- offline source fixture"]
    assert kit.debug_editors()["editors"]
    assert {p.relative_to(kit.profile).as_posix(): p.read_bytes()
            for p in kit.profile.rglob("*") if p.is_file()} == before
    assert kit.profile.exists() is unowned
    assert not kit.workspace.exists()


@pytest.mark.parametrize("tracked,state", [(True, "running"), (False, "closed"), (None, "unknown")])
def test_bridge_status_distinguishes_tracked_game_from_connection(kit, monkeypatch, tracked, state):
    kit.profile_prepare()
    (kit.profile / "console.txt").write_text("previous session\n")
    monkeypatch.setattr(kit, "_tracked_game_running", lambda: tracked)
    before = {p.relative_to(kit.profile).as_posix(): p.read_bytes()
              for p in kit.profile.rglob("*") if p.is_file()}
    status = kit.bridge_status()
    assert status["ready"] is False
    assert status["game_state"] == state
    assert kit.logs_read()["lines"] == ["previous session"]
    assert {p.relative_to(kit.profile).as_posix(): p.read_bytes()
            for p in kit.profile.rglob("*") if p.is_file()} == before


def test_fresh_ready_heartbeat_does_not_need_a_process_probe(kit, monkeypatch):
    import time
    kit.profile_prepare()
    (kit.profile / "Lua/pzt-status.txt").write_text(json.dumps({
        "ready": True, "timestamp_ms": time.time() * 1000, "god_mode": True}))
    monkeypatch.setattr(kit, "_tracked_game_running", lambda: pytest.fail("Unneeded process probe"))
    assert kit.bridge_status()["game_state"] == "world_loaded"
    assert kit.bridge_status()["ready"] is True


def test_probe_failure_reports_unknown_and_blocks_profile_writes(kit, monkeypatch):
    kit.profile_prepare()
    def unavailable():
        raise ValueError("Could not inspect the tracked game process")
    monkeypatch.setattr(kit, "_tracked_game_running", unavailable)
    assert kit.bridge_status()["game_state"] == "unknown"
    with pytest.raises(ValueError, match="Could not inspect"):
        kit.profile_prepare()


def test_pid_file_is_absent_does_not_claim_game_closed(kit):
    kit.profile_prepare()
    assert kit._tracked_game_running() is None
    assert kit.bridge_status()["game_state"] == "unknown"
