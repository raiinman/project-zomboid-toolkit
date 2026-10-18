"""Shared, transport-independent tools. Game files are always read-only."""

from __future__ import annotations

import hashlib
import csv
import inspect
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import secrets
import shutil
import stat
import subprocess
import time
from typing import get_type_hints
import uuid


OWNER = "pztoolkit-v1"
TOOL_NAMES = (
    "doctor", "mod_create", "mod_check", "mod_deploy", "source_search",
    "source_read", "profile_prepare", "game_launch", "logs_read", "bridge_status",
    "harness_run", "folders_detect", "lua_execute", "god_mode", "debug_editors", "editor_open", "bridge_install",
)

GAME_TOOL_NAMES = (
    "doctor", "bridge_install", "game_launch", "bridge_status", "logs_read",
    "source_search", "source_read", "lua_execute", "god_mode", "debug_editors", "editor_open",
)

# Signatures inspected in shipped DebugUIs/DebugMenu/ISDebugMenu.lua.
DEBUG_EDITORS = {
    "debug": ("Debug menu", "require 'DebugUIs/DebugMenu/ISDebugMenu'; "
              "assert(ISDebugMenu and type(ISDebugMenu.OnOpenPanel) == 'function', 'Debug menu unavailable'); ISDebugMenu.OnOpenPanel()"),
    "vehicle": ("Vehicle editor", "assert(type(showVehicleEditor) == 'function', 'Vehicle editor unavailable'); showVehicleEditor(nil)"),
    "attachment": ("Attachment editor", "assert(type(showAttachmentEditor) == 'function', 'Attachment editor unavailable'); showAttachmentEditor()"),
    "animation": ("Animation viewer", "assert(type(showAnimationViewer) == 'function', 'Animation viewer unavailable'); showAnimationViewer()"),
    "world_map": ("World map editor", "assert(type(showWorldMapEditor) == 'function', 'World map editor unavailable'); showWorldMapEditor(nil)"),
}


def confined(root: Path, relative: str) -> Path:
    """Resolve a relative path, including symlinks, within its allowed root."""
    if not relative or Path(relative).is_absolute() or PureWindowsPath(relative).drive:
        raise ValueError("Expected a relative path inside the configured root")
    candidate = root / relative.replace("\\", "/")
    for component in (candidate, *candidate.parents):
        if component == root:
            break
        if linked(component):
            raise ValueError("Linked paths are not permitted inside configured roots")
    path = candidate.resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Path escapes the configured root")
    return path


def linked(path: Path) -> bool:
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0)
                                         & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except FileNotFoundError:
        return False


def mod_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value):
        raise ValueError("Mod ID must start with a letter and contain only letters, digits, underscores (max 64)")
    if value.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("Mod ID is a reserved filesystem name")
    return value


def atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> dict:
    # shortcut: local protocol documents are capped at 1 MiB; stream if evidence grows.
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Protocol document exceeds 1 MiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


class Toolkit:
    def __init__(self, config_path: str | Path, *, tool_names=None):
        self.tool_names = tuple(tool_names or TOOL_NAMES)
        self.config_path = Path(config_path).resolve()
        config = read_json(self.config_path)
        roots = []
        for key in ("game_dir", "profile_dir", "workspace_dir"):
            value = config.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Configuration requires {key}")
            roots.append((self.config_path.parent / value).resolve())
        self.game, self.profile, self.workspace = roots
        for i, left in enumerate(roots):
            for right in roots[i + 1:]:
                if left.is_relative_to(right) or right.is_relative_to(left):
                    raise ValueError("Game, profile, and workspace roots must not overlap")
        normal_profile = (Path.home() / "Zomboid").resolve()
        if self.profile.is_relative_to(normal_profile) or normal_profile.is_relative_to(self.profile):
            raise ValueError("Choose an isolated profile outside the normal Zomboid profile")

    def tools(self) -> dict:
        return {name: getattr(self, name) for name in self.tool_names}

    def schemas(self) -> list[dict]:
        result = []
        for name, fn in self.tools().items():
            hints = get_type_hints(fn)
            properties, required = {}, []
            for param in inspect.signature(fn).parameters.values():
                prop = {"type": {str: "string", int: "integer", float: "number", bool: "boolean"}[hints[param.name]]}
                if param.default is inspect.Parameter.empty:
                    required.append(param.name)
                else:
                    prop["default"] = param.default
                properties[param.name] = prop
            result.append({"name": name, "description": inspect.getdoc(fn) or name,
                           "inputSchema": {"type": "object", "properties": properties,
                                           "required": required, "additionalProperties": False}})
        return result

    def call(self, name: str, arguments: dict) -> dict:
        if name not in self.tools():
            raise ValueError(f"Unknown tool: {name}")
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a JSON object")
        fn = self.tools()[name]
        try:
            bound = inspect.signature(fn).bind(**arguments)
        except TypeError as exc:
            raise ValueError(str(exc)) from exc
        for key, value in bound.arguments.items():
            expected = get_type_hints(fn)[key]
            valid = type(value) is expected or (expected is float and type(value) is int)
            if not valid or (expected is float and not math.isfinite(value)):
                raise ValueError(f"Invalid type or value for {key}: expected {expected.__name__}")
        return fn(**arguments)

    def folders_detect(self) -> dict:
        """Find installed game folders and suggest setup paths without writing files."""
        from .discovery import detect_folders
        return detect_folders({"game_dir": str(self.game), "workspace_dir": str(self.workspace),
                               "profile_dir": str(self.profile)}, self.config_path.parent)

    def doctor(self) -> dict:
        """Inspect configured paths and installed build without modifying them."""
        version = self.game / "version.txt"
        return {"game_dir": str(self.game), "profile_dir": str(self.profile),
                "workspace_dir": str(self.workspace), "game_found": (self.game / "media/lua").is_dir(),
                "build": version.read_text(encoding="utf-8").strip()[:200] if version.is_file() else None,
                "profile_prepared": (self.profile / ".pztoolkit-profile").is_file(),
                "build_note": "Runtime bridge heartbeat is authoritative when no installation version.txt exists"}

    def mod_create(self, name: str) -> dict:
        """Create a Build 42 Lua mod and a matching in-game smoke scenario."""
        name = mod_id(name)
        target = confined(self.workspace, f"mods/{name}")
        scenario = confined(self.workspace, f"scenarios/{name}_smoke.lua")
        if target.exists() or scenario.exists():
            raise ValueError("Mod or scenario already exists; refusing to overwrite")
        (target / "42/media/lua/client").mkdir(parents=True)
        (target / "common").mkdir()
        (target / "common/.keep").write_text("", encoding="utf-8")
        (target / "42/mod.info").write_text(f"name={name}\nid={name}\ndescription=Toolkit development mod\n", encoding="utf-8")
        (target / f"42/media/lua/client/{name}.lua").write_text(
            f'_G["{name}"] = {{ loaded = true }}\nprint("[{name}] loaded")\n', encoding="utf-8")
        scenario.parent.mkdir(parents=True, exist_ok=True)
        scenario.write_text(f'assert(_G["{name}"] and _G["{name}"].loaded, "Mod did not load")\n'
                            'assert(getPlayer(), "Load a single-player test world first")\n'
                            f'return "{name} loaded in the game"\n', encoding="utf-8")
        return {"id": name, "mod": f"mods/{name}", "scenario": f"scenarios/{name}_smoke.lua"}

    def mod_check(self, mod: str) -> dict:
        """Check Build 42 layout and metadata. This does not validate Lua execution."""
        target = confined(self.workspace, mod)
        errors = []
        if not target.is_dir():
            raise ValueError("Mod directory does not exist")
        for directory, dirs, files in os.walk(target, followlinks=False):
            if any(linked(Path(directory) / name) for name in (*dirs, *files)):
                errors.append("Mod contains a symlink or junction")
                break
        info = target / "42/mod.info"
        fields = {}
        if info.is_file() and info.resolve().is_relative_to(target):
            for line in info.read_text(encoding="utf-8-sig").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    fields[key.strip()] = value.strip()
        else:
            errors.append("Missing 42/mod.info")
        for key in ("name", "id"):
            if not fields.get(key):
                errors.append(f"Missing mod.info {key}")
        try:
            mod_id(fields.get("id", ""))
        except ValueError as exc:
            errors.append(str(exc))
        if not (target / "common").is_dir():
            errors.append("Missing common directory")
        if fields.get("id") == "PZToolkitBridge":
            errors.append("PZToolkitBridge is reserved for the harness")
        return {"ok": not errors, "id": fields.get("id"), "errors": errors,
                "warnings": ["Lua syntax and runtime behavior require an in-game harness run"]}

    def _owned_profile(self) -> None:
        marker = self.profile / ".pztoolkit-profile"
        if not marker.is_file() or marker.read_text(encoding="utf-8") != OWNER:
            raise ValueError("Profile is not toolkit-owned; run profile_prepare with a new isolated directory")

    def _profile_path(self, relative: str) -> Path:
        return confined(self.profile, relative)

    def _deploy(self, source: Path, identifier: str) -> Path:
        self._owned_profile()
        target = self._profile_path(f"mods/{mod_id(identifier)}")
        marker = target / ".pztoolkit-owned"
        if target.exists() and (not marker.is_file() or marker.read_text(encoding="utf-8") != OWNER):
            raise ValueError("Deployment target exists and is not toolkit-owned")
        staging = self._profile_path(f"staging/{uuid.uuid4().hex}")
        staging.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, staging)
        (staging / ".pztoolkit-owned").write_text(OWNER, encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = None
        if target.exists():
            backup = self._profile_path(f"backups/{identifier}-{uuid.uuid4().hex}")
            backup.parent.mkdir(parents=True, exist_ok=True)
            target.rename(backup)
        try:
            staging.rename(target)
        except OSError:
            if backup is not None:
                backup.rename(target)
            raise
        return target

    def _enable(self, identifier: str) -> None:
        path = self._profile_path("mods/default.txt")
        text = path.read_text(encoding="utf-8") if path.exists() else "VERSION = 1,\nmods\n{\n}\nmaps\n{\n}\n"
        match = re.search(r"(?ms)^mods\s*\{(.*?)\}", text)
        if not match:
            raise ValueError("Unsupported default.txt format in isolated profile")
        ids = re.findall(r"\bmod\s*=\s*([^,\s]+)", match.group(1))
        if identifier not in ids:
            body = match.group(1) + f"    mod = {identifier},\n"
            atomic_text(path, text[:match.start(1)] + body + text[match.end(1):])

    def _tracked_game_running(self) -> bool | None:
        """Inspect only the recorded game PID, without desktop input or signals on Windows."""
        pid_file = self._profile_path("pzt-game.pid")
        if pid_file.exists():
            pid = int(pid_file.read_text())
            if pid <= 0:
                raise ValueError("Invalid tracked game process ID")
            if os.name == "nt":
                # Windows signal 0 is CTRL_C_EVENT, not a process-existence probe.
                try:
                    listing = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                             capture_output=True, text=True, check=True, timeout=2,
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                except (OSError, subprocess.SubprocessError) as exc:
                    raise ValueError("Could not inspect the tracked game process") from exc
                running = any(len(row) > 1 and row[1] == str(pid) and
                              row[0].lower() == "projectzomboid64.exe"
                              for row in csv.reader(listing.stdout.splitlines()))
            else:
                try:
                    os.kill(pid, 0)
                    running = True
                except ProcessLookupError:
                    running = False
                except OSError as exc:
                    raise ValueError("Could not inspect the tracked game process") from exc
            return running
        return None

    def _ensure_game_stopped(self) -> None:
        """Refuse bridge deployment or another launch while the tracked game runs."""
        if self._tracked_game_running():
            raise ValueError("A tracked game process is already running")

    def _profile_prepared(self) -> bool:
        marker = self._profile_path(".pztoolkit-profile")
        return marker.is_file() and marker.read_text(encoding="utf-8") == OWNER

    def profile_prepare(self) -> dict:
        """Initialize an isolated game profile and install/enable the local debug bridge."""
        self._ensure_game_stopped()
        marker = self.profile / ".pztoolkit-profile"
        if self.profile.exists() and not marker.exists() and any(self.profile.iterdir()):
            raise ValueError("Refusing to claim a nonempty profile without toolkit ownership")
        self.profile.mkdir(parents=True, exist_ok=True)
        if marker.exists():
            self._owned_profile()
        else:
            marker.write_text(OWNER, encoding="utf-8")
        lua_dir = self._profile_path("Lua")
        lua_dir.mkdir(parents=True, exist_ok=True)
        token = self._profile_path("Lua/pzt-token.txt")
        if not token.exists():
            atomic_text(token, secrets.token_hex(32) + "\n")
        source = Path(__file__).parent / "assets/bridge"
        if not (source / "42/mod.info").is_file():
            raise ValueError("Bridge package assets are missing")
        self._deploy(source, "PZToolkitBridge")
        self._enable("PZToolkitBridge")
        return {"ok": True, "profile_dir": str(self.profile), "bridge": "PZToolkitBridge",
                "first_launch_requires_mod_confirmation": True,
                "next_step": "Deploy a mod, launch this profile, enable the bridge/mod in Mods, then create a single-player test world"}

    def bridge_install(self) -> dict:
        """Install and enable the toolkit bridge in its owned isolated game profile."""
        result = self.profile_prepare()
        result["next_step"] = "Launch the isolated debug game, enable PZ Toolkit Bridge and load a single-player world"
        return result

    def mod_deploy(self, mod: str) -> dict:
        """Deploy a checked mod into the owned isolated profile, preserving its previous deployment."""
        check = self.mod_check(mod)
        if not check["ok"]:
            raise ValueError("; ".join(check["errors"]))
        self._owned_profile()
        target = self._deploy(confined(self.workspace, mod), check["id"])
        self._enable(check["id"])
        return {"ok": True, "id": check["id"], "destination": str(target),
                "restart_required": True}

    def source_search(self, query: str, limit: int = 30) -> dict:
        """Search installed Lua and script text literally; return bounded file/line matches."""
        if not query or len(query) > 300 or not 1 <= limit <= 200:
            raise ValueError("Query must be 1-300 characters; limit must be 1-200")
        root = confined(self.game, "media")
        matches = []
        for subtree in ("lua", "scripts"):
            folder = confined(root, subtree)
            for path in sorted(folder.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in (".lua", ".txt"):
                    continue
                if not path.resolve().is_relative_to(root) or path.stat().st_size > 2 * 1024 * 1024:
                    continue
                for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if query.casefold() in line.casefold():
                        matches.append({"path": path.relative_to(root).as_posix(), "line": number, "text": line[:500]})
                        if len(matches) >= limit:
                            return {"matches": matches, "limit_reached": True}
        return {"matches": matches, "limit_reached": False}

    def source_read(self, path: str, start: int = 1, lines: int = 100) -> dict:
        """Read a bounded excerpt from installed media/lua or media/scripts text."""
        if start < 1 or not 1 <= lines <= 400:
            raise ValueError("start must be positive; lines must be 1-400")
        root = confined(self.game, "media")
        target = confined(root, path)
        relative = target.relative_to(root)
        if relative.parts[0] not in ("lua", "scripts") or target.suffix.lower() not in (".lua", ".txt"):
            raise ValueError("Only Lua and script source files may be read")
        if target.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Source file exceeds 2 MiB")
        content = target.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"path": relative.as_posix(), "start": start, "lines": content[start - 1:start - 1 + lines]}

    def game_launch(self) -> dict:
        """Launch isolated debug single-player testing with god mode enabled on character load."""
        self._owned_profile()
        executable = self.game / "ProjectZomboid64.exe"
        if not executable.is_file():
            raise ValueError("Windows ProjectZomboid64.exe was not found in game_dir")
        self._ensure_game_stopped()
        pid_file = self._profile_path("pzt-game.pid")
        bridge_relative = "42/media/lua/client/PZToolkitBridge.lua"
        source = Path(__file__).parent / "assets/bridge" / bridge_relative
        installed = self._profile_path("mods/PZToolkitBridge/" + bridge_relative)
        if (not installed.is_file() or installed.stat().st_size != source.stat().st_size
                or installed.read_bytes() != source.read_bytes()):
            self.profile_prepare()
        else:
            self._enable("PZToolkitBridge")
        args = [str(executable), "-debug", f"-cachedir={self.profile}", "-modfolders", "mods"]
        process = subprocess.Popen(args, cwd=self.game, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        atomic_text(pid_file, str(process.pid))
        return {"ok": True, "pid": process.pid, "profile_dir": str(self.profile),
                "debug": True, "god_mode_on_spawn": True,
                "next_step": "Enable PZ Toolkit Bridge and load a disposable single-player world. God mode turns on when your character loads; check bridge_status."}

    def logs_read(self, lines: int = 100) -> dict:
        """Read the tail of console.txt from the isolated profile only."""
        if not 1 <= lines <= 500:
            raise ValueError("lines must be 1-500")
        if not self._profile_prepared():
            return {"lines": [], "exists": False, "reason": "profile_not_prepared",
                    "message": "No Toolkit test-session log is available yet. Offline source tools still work."}
        path = self._profile_path("console.txt")
        if not path.exists():
            return {"lines": [], "exists": False, "reason": "log_not_created",
                    "message": "No test-session log exists yet. Start a test session to create one."}
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 256 * 1024))
            content = stream.read(256 * 1024).decode("utf-8", errors="replace")
        return {"lines": content.splitlines()[-lines:], "exists": True}

    def bridge_status(self) -> dict:
        """Check a fresh heartbeat from the debug bridge in a loaded local test world."""
        if not self._profile_prepared():
            return {"ready": False, "reason": "profile_not_prepared", "game_state": "unknown",
                    "next_step": "Offline tools are available. Launch Project Zomboid (test profile) when you need live controls."}
        try:
            status = read_json(self._profile_path("Lua/pzt-status.txt"))
            timestamp = status.get("timestamp_ms")
            age = time.time() * 1000 - timestamp if type(timestamp) in (int, float) else float("inf")
            ready = status.get("ready") is True and math.isfinite(age) and -1000 <= age <= 5000
        except (OSError, ValueError):
            status, ready = {}, False
        game_state = "world_loaded" if ready else "unknown"
        if not ready:
            try:
                tracked = self._tracked_game_running()
                game_state = "running" if tracked is True else "closed" if tracked is False else "unknown"
            except (OSError, ValueError):
                pass
        if game_state == "closed":
            status = {"reason": "game_closed"}
            return {**status, "ready": False, "game_state": game_state,
                    "next_step": "Offline tools are available. Launch Project Zomboid (test profile) to use live controls."}
        return {**status, "ready": ready, "game_state": game_state, "next_step": None if ready else
                "Enable the bridge in the isolated profile and keep a debug single-player world loaded and unpaused"}

    def harness_run(self, scenario: str, timeout: float = 30) -> dict:
        """Run trusted local Lua assertions in the game and save a correlated JSON report."""
        if not 0.1 <= timeout <= 300:
            raise ValueError("timeout must be between 0.1 and 300 seconds")
        path = confined(self.workspace, scenario)
        if path.suffix.lower() != ".lua" or path.stat().st_size > 60 * 1024:
            raise ValueError("Scenario must be a Lua file no larger than 60 KiB")
        code = path.read_text(encoding="utf-8-sig")
        return self._execute(code, timeout, scenario)

    def lua_execute(self, code: str, timeout: float = 30) -> dict:
        """Execute trusted inline Lua in the loaded debug world without scenario or report files."""
        if not isinstance(code, str) or not code.strip() or len(code.encode("utf-8")) > 60 * 1024:
            raise ValueError("code must be nonempty Lua no larger than 60 KiB")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0.1 <= timeout <= 300:
            raise ValueError("timeout must be between 0.1 and 300 seconds")
        return self._execute(code, timeout)

    def god_mode(self, enabled: bool = True) -> dict:
        """Set and verify the loaded player's god mode through the authenticated debug bridge."""
        if type(enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        return self._execute(f"PZT-OP/1\ngod_mode\n{str(enabled).lower()}", 30, operation=True)

    def debug_editors(self) -> dict:
        """List supported built-in debug editors without opening windows or writing files."""
        return {"editors": [{"id": key, "name": value[0]} for key, value in DEBUG_EDITORS.items()],
                "requires": "A connected, loaded debug single-player world",
                "evidence": "Opening is a game-side request, not verification that a window is visible"}

    def editor_open(self, editor: str) -> dict:
        """Request one allowlisted built-in editor in the connected debug game."""
        if not isinstance(editor, str) or editor not in DEBUG_EDITORS:
            raise ValueError("Unknown editor; choose an id returned by debug_editors")
        return self._execute(f"PZT-OP/1\neditor_open\n{editor}", 30, operation=True)

    def _execute(self, code: str, timeout: float, scenario: str | None = None, *, operation: bool = False) -> dict:
        """Shared authenticated wire transport; only legacy scenarios persist reports."""
        status = self.bridge_status()
        if not status["ready"]:
            raise ValueError(f"Bridge is not ready ({status.get('reason', 'no fresh heartbeat')}): {status['next_step']}")
        if operation and status.get("operations_available") is not True:
            raise ValueError("Bridge needs an update for built-in commands. Close the test game, install the bridge, and relaunch")
        if not operation and (status.get("lua_compiler") is False or status.get("lua_execution_available") is False):
            raise ValueError("Lua compiler unavailable in this game build. Built-in god mode and editor commands remain available")
        lock = self._profile_path("Lua/pzt-run.lock")
        try:
            lock_file = lock.open("x", encoding="utf-8")
        except FileExistsError as exc:
            raise ValueError("Another harness run holds pzt-run.lock; recover it only after confirming no run is active") from exc
        request = self._profile_path("Lua/pzt-request.txt")
        response = self._profile_path("Lua/pzt-response.txt")
        identifier = uuid.uuid4().hex
        started = time.monotonic()
        log_path = self._profile_path("console.txt")
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        log_prefix = b""
        if log_offset:
            with log_path.open("rb") as stream:
                log_prefix = stream.read(min(4096, log_offset))
        report = {"id": identifier, "sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                  "status": "timed_out", "ok": False, "message": "No matching game response before deadline",
                  "game_build": status.get("build"), "execution_contract":
                  "predefined bridge operation" if operation else "synchronous Lua assertions"}
        if scenario is not None:
            report["scenario"] = scenario
        try:
            with lock_file:
                lock_file.write(identifier)
            token = self._profile_path("Lua/pzt-token.txt").read_text(encoding="utf-8").strip()
            if not re.fullmatch(r"[0-9a-f]{64}", token):
                raise ValueError("Invalid local bridge token")
            expiry = int((time.time() + timeout) * 1000)
            atomic_text(request, f"{token}\n{identifier}\n{expiry}\n{code}\n")
            while time.monotonic() - started < timeout:
                try:
                    result = read_json(response)
                    if result.get("id") == identifier:
                        if type(result.get("ok")) is not bool or not isinstance(result.get("message"), str):
                            report.update(status="invalid_response", message="Malformed matching bridge response")
                        else:
                            report.update(status="passed" if result["ok"] else "failed", ok=result["ok"], message=result["message"])
                        break
                except (OSError, ValueError):
                    pass
                time.sleep(0.05)
        finally:
            # Expired/pending work must not execute when the player later resumes.
            try:
                atomic_text(request, "")
            finally:
                lock.unlink(missing_ok=True)
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["logs"] = []
        report["log_rollover_detected"] = False
        report["logs_truncated"] = False
        if log_path.exists():
            with log_path.open("rb") as stream:
                size = log_path.stat().st_size
                prefix = stream.read(len(log_prefix))
                rollover = size < log_offset or prefix != log_prefix
                offset = 0 if rollover else log_offset
                report["log_rollover_detected"] = rollover
                report["logs_truncated"] = size - offset > 256 * 1024
                stream.seek(offset)
                report["logs"] = stream.read(256 * 1024).decode("utf-8", errors="replace").splitlines()
        if scenario is not None:
            destination = self._profile_path(f"reports/{identifier}.json")
            destination.parent.mkdir(parents=True, exist_ok=True)
            report["report"] = str(destination)
            atomic_text(destination, json.dumps(report, indent=2, ensure_ascii=False))
        return report
