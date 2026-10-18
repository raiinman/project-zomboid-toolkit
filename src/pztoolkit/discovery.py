"""Bounded, read-only discovery of local game installations and safe defaults."""

from __future__ import annotations

import os
from pathlib import Path
import re

MAX_VDF_BYTES = 512 * 1024
MAX_LIBRARIES = 64
GAME_MARKERS = ("ProjectZomboid64.exe", "ProjectZomboid32.exe", "ProjectZomboid.exe")


def _registry_steam_roots() -> list[Path]:
    try:
        import winreg
    except ImportError:
        return []
    roots = []
    for hive, key, value, flags in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath", 0),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Valve\Steam", "InstallPath", 0),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Valve\Steam", "InstallPath", winreg.KEY_WOW64_32KEY),
    ):
        try:
            with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | flags) as handle:
                path, _ = winreg.QueryValueEx(handle, value)
            if isinstance(path, str) and path.strip():
                roots.append(Path(path))
        except OSError:
            continue
    return roots


def _steam_roots() -> list[Path]:
    roots = _registry_steam_roots()
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        if value := os.environ.get(variable):
            roots.append(Path(value) / "Steam")
    roots.extend((Path("C:/Program Files/Steam"), Path("C:/Program Files (x86)/Steam")))
    return roots


def _common_game_dirs() -> list[Path]:
    paths = [Path("C:/Games/ProjectZomboid"), Path("C:/GOG Games/Project Zomboid")]
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        if value := os.environ.get(variable):
            paths.extend((Path(value) / "GOG Galaxy/Games/Project Zomboid", Path(value) / "GOG Games/Project Zomboid"))
    return paths


def _absolute(path: Path) -> Path | None:
    try:
        return path.expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _verified_game(path: Path) -> bool:
    try:
        return (path / "media/lua").is_dir() and any((path / marker).is_file() for marker in GAME_MARKERS)
    except (OSError, ValueError):
        return False


def _library_paths(steam_root: Path) -> list[Path]:
    """Read only Steam's known index, never enumerate drives or directory trees."""
    try:
        with (steam_root / "steamapps/libraryfolders.vdf").open("rb") as handle:
            raw = handle.read(MAX_VDF_BYTES + 1)
        if len(raw) > MAX_VDF_BYTES:
            return []
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError):
        return []
    paths = []
    # Modern indexes use "path" fields; old indexes map numeric keys to paths.
    for match in re.finditer(r'"(path|\d+)"\s*"((?:[^"\\]|\\.)*)"', text, re.IGNORECASE):
        value = re.sub(r'\\([\\"])', r'\1', match.group(2))
        candidate = Path(value)
        if candidate.is_absolute():
            paths.append(candidate)
        if len(paths) >= MAX_LIBRARIES:
            break
    return paths


def detect_folders(current: dict[str, str], data_dir: Path) -> dict:
    """Suggest folders without creating directories, writing config, or game reads beyond markers."""
    candidates: list[dict[str, str]] = []
    seen_games: set[str] = set()
    seen_roots: set[str] = set()
    notes = []

    def add(path: Path, source: str) -> bool:
        resolved = _absolute(path)
        if resolved is None or not _verified_game(resolved):
            return False
        key = os.path.normcase(str(resolved))
        if key not in seen_games:
            candidates.append({"path": str(resolved), "source": source})
            seen_games.add(key)
        return True

    current_game = current.get("game_dir", "")
    current_valid = bool(current_game.strip()) and add(Path(current_game), "Current setup")
    for root in _steam_roots():
        root = _absolute(root)
        if root is None or os.path.normcase(str(root)) in seen_roots:
            continue
        seen_roots.add(os.path.normcase(str(root)))
        add(root / "steamapps/common/ProjectZomboid", "Steam")
        for library in _library_paths(root):
            add(library / "steamapps/common/ProjectZomboid", "Steam library")
    for path in _common_game_dirs():
        add(path, "Common install location")

    if current_valid or len(candidates) == 1:
        game_dir = candidates[0]["path"]
    else:
        game_dir = ""
        notes.append("Multiple game installations found. Choose the installation to use." if candidates else "No verified Project Zomboid installation found. Browse to the game folder.")
    if current_game.strip() and not current_valid:
        notes.append("The current game folder could not be verified.")
    base = _absolute(data_dir)
    if base is None:
        raise ValueError("The application data folder could not be resolved")
    normal_profile = _absolute(Path.home() / "Zomboid")
    needs_defaults = not current.get("workspace_dir", "") or not current.get("profile_dir", "")
    if needs_defaults and normal_profile is not None and base.is_relative_to(normal_profile):
        raise ValueError("Automatic folder defaults must stay outside the normal Zomboid profile")
    return {
        "game_candidates": candidates,
        "suggested": {
            "game_dir": game_dir,
            "workspace_dir": current.get("workspace_dir", "") or str(base / "workspace"),
            "profile_dir": current.get("profile_dir", "") or str(base / "game-profile"),
        },
        "notes": notes,
    }
