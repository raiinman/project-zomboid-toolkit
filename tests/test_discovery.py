import pytest

from pztoolkit import discovery


@pytest.fixture(autouse=True)
def isolated_discovery(monkeypatch):
    monkeypatch.setattr(discovery, "_steam_roots", lambda: [])
    monkeypatch.setattr(discovery, "_common_game_dirs", lambda: [])


def game(path):
    (path / "media/lua").mkdir(parents=True)
    (path / "ProjectZomboid64.exe").write_bytes(b"fixture")
    return path


def test_missing_install_and_defaults_do_not_write(tmp_path):
    data = tmp_path / "not-created"
    result = discovery.detect_folders({}, data)
    assert result["game_candidates"] == []
    assert result["suggested"] == {"game_dir": "", "workspace_dir": str(data / "workspace"), "profile_dir": str(data / "game-profile")}
    assert result["notes"]
    assert not data.exists()


@pytest.mark.parametrize("nested", [False, True])
def test_default_folders_never_use_the_normal_zomboid_profile(tmp_path, monkeypatch, nested):
    monkeypatch.setattr(discovery.Path, "home", lambda: tmp_path)
    data = tmp_path / "Zomboid"
    if nested:
        data = data / "toolkit"
    with pytest.raises(ValueError, match="normal Zomboid profile"):
        discovery.detect_folders({}, data)
    assert not data.exists()


def test_existing_paths_are_preserved_even_when_config_is_in_normal_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery.Path, "home", lambda: tmp_path)
    result = discovery.detect_folders({"workspace_dir": "existing-workspace", "profile_dir": "existing-profile"}, tmp_path / "Zomboid")
    assert result["suggested"]["profile_dir"] == "existing-profile"
    assert result["suggested"]["workspace_dir"] == "existing-workspace"


def test_verified_current_wins_and_existing_work_folders_are_preserved(tmp_path, monkeypatch):
    current = game(tmp_path / "current")
    other = game(tmp_path / "other")
    monkeypatch.setattr(discovery, "_common_game_dirs", lambda: [other])
    config = {"game_dir": str(current), "workspace_dir": "existing-workspace", "profile_dir": "existing-isolated-profile"}
    before = config.copy()
    result = discovery.detect_folders(config, tmp_path / "data")
    assert result["suggested"] == config
    assert result["game_candidates"][0]["source"] == "Current setup"
    assert len(result["game_candidates"]) == 2
    assert config == before


def test_ambiguous_installs_require_a_choice(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery, "_common_game_dirs", lambda: [game(tmp_path / "a"), game(tmp_path / "b")])
    result = discovery.detect_folders({}, tmp_path)
    assert result["suggested"]["game_dir"] == ""
    assert len(result["game_candidates"]) == 2
    assert "Multiple" in result["notes"][0]


def test_game_requires_both_lua_and_executable(tmp_path, monkeypatch):
    lua_only = tmp_path / "lua-only"
    (lua_only / "media/lua").mkdir(parents=True)
    exe_only = tmp_path / "exe-only"
    exe_only.mkdir()
    (exe_only / "ProjectZomboid64.exe").touch()
    valid = game(tmp_path / "valid")
    monkeypatch.setattr(discovery, "_common_game_dirs", lambda: [lua_only, exe_only, valid, valid / "."])
    result = discovery.detect_folders({"game_dir": str(lua_only)}, tmp_path)
    assert result["game_candidates"] == [{"path": str(valid), "source": "Common install location"}]
    assert result["suggested"]["game_dir"] == str(valid)
    assert any("current" in note for note in result["notes"])


@pytest.mark.parametrize("modern", [True, False])
def test_secondary_steam_library_and_duplicate_roots(tmp_path, monkeypatch, modern):
    steam = tmp_path / "Steam"
    (steam / "steamapps").mkdir(parents=True)
    library = tmp_path / "OtherLibrary"
    target = game(library / "steamapps/common/ProjectZomboid")
    escaped = str(library).replace("\\", "\\\\")
    entry = f'"1" {{ "path" "{escaped}" }}' if modern else f'"1" "{escaped}"'
    (steam / "steamapps/libraryfolders.vdf").write_text(f'"libraryfolders" {{ {entry} {entry} }}', encoding="utf-8")
    monkeypatch.setattr(discovery, "_steam_roots", lambda: [steam, steam])
    result = discovery.detect_folders({}, tmp_path)
    assert result["game_candidates"] == [{"path": str(target), "source": "Steam library"}]
    assert result["suggested"]["game_dir"] == str(target)


@pytest.mark.parametrize("payload", [b'"path" "unterminated', b"\xff\xfe", b"x" * (discovery.MAX_VDF_BYTES + 1)], ids=["malformed", "invalid-utf8", "oversized"])
def test_bad_or_oversized_library_index_is_ignored(tmp_path, monkeypatch, payload):
    (tmp_path / "steamapps").mkdir()
    (tmp_path / "steamapps/libraryfolders.vdf").write_bytes(payload)
    monkeypatch.setattr(discovery, "_steam_roots", lambda: [tmp_path])
    assert discovery.detect_folders({}, tmp_path)["game_candidates"] == []


def test_library_count_is_bounded_and_relative_entries_ignored(tmp_path):
    (tmp_path / "steamapps").mkdir()
    entries = ['"path" "relative"']
    entries.extend(f'"path" "{(tmp_path / str(i)).as_posix()}"' for i in range(100))
    (tmp_path / "steamapps/libraryfolders.vdf").write_text("\n".join(entries))
    assert len(discovery._library_paths(tmp_path)) == discovery.MAX_LIBRARIES


def test_inaccessible_index_does_not_hide_a_primary_install(tmp_path, monkeypatch):
    primary = game(tmp_path / "steamapps/common/ProjectZomboid")
    # A directory cannot be opened as a regular VDF file on either CI platform.
    (tmp_path / "steamapps/libraryfolders.vdf").mkdir()
    monkeypatch.setattr(discovery, "_steam_roots", lambda: [tmp_path])
    result = discovery.detect_folders({}, tmp_path / "data")
    assert result["suggested"]["game_dir"] == str(primary)
    assert result["game_candidates"] == [{"path": str(primary), "source": "Steam"}]


def test_registry_and_environment_roots_are_available_without_disk_scan(tmp_path, monkeypatch):
    # Exercise the production aggregator while isolating all machine state.
    monkeypatch.undo()
    monkeypatch.setattr(discovery, "_registry_steam_roots", lambda: [tmp_path / "RegistrySteam"])
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "Programs"))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "Programs32"))
    roots = discovery._steam_roots()
    assert tmp_path / "RegistrySteam" in roots
    assert tmp_path / "Programs/Steam" in roots
    assert tmp_path / "Programs32/Steam" in roots
