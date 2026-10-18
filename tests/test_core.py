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
