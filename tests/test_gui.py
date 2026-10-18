"""Real Tk widgets against temporary profiles and simulated game replies."""
import json
import sys
import threading
import time

import pytest

tk = pytest.importorskip("tkinter")
from tkinter import ttk
from pztoolkit.core import GAME_TOOL_NAMES
from pztoolkit.gui import Application, EDITORS

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows GUI acceptance")


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(tmp_path, tk_root):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"game_dir": "game", "workspace_dir": "workspace", "profile_dir": "profile"}))
    root = tk.Toplevel(tk_root)
    root.withdraw()
    application = Application(root, config)
    yield application
    application.editor.edit_modified(False)
    application.lua_dirty = False
    application.close()


def press(app, label):
    next(button for button in app.actions if button.cget("text") == label).invoke()


def wait(app):
    deadline = time.monotonic() + 5
    while app.busy and time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.01)
    assert not app.busy, "GUI did not deliver the worker result"
    return app.last_result


def test_toolbelt_opens_without_mod_folder_or_scenario_controls(app):
    assert [app.tabs.tab(page, "text") for page in app.tabs.tabs()] == ["Connection", "Game tools"]
    labels = [button.cget("text") for button in app.actions]
    assert "Connect to game" in labels
    assert "Launch Project Zomboid (test profile)" in labels
    assert not any(word in label.lower() for label in labels for word in ("create mod", "folder", "deploy", "scenario", "save setup"))
    assert not app.details_open.get()
    assert "Not checked" in app.status.get()
    assert not app.connected
    assert set(app.toolkit.tools()) == set(GAME_TOOL_NAMES)
    assert not app.toolkit.workspace.exists()
    assert not app.toolkit.profile.exists()


def test_connect_installs_only_bridge_and_preserves_saved_configuration(app):
    before = app.config.read_bytes()
    press(app, "Connect to game")
    result = wait(app)
    assert not result["ready"]
    assert "Not connected" in app.status.get()
    assert app.config.read_bytes() == before
    assert (app.toolkit.profile / "mods/PZToolkitBridge/42/mod.info").is_file()
    assert not app.toolkit.workspace.exists()
    assert not app.connected
    assert "launch" in app.next_step.get().lower()


def test_connect_to_existing_bridge_does_not_redeploy_it(app):
    press(app, "Connect to game")
    wait(app)
    script = app.toolkit.profile / "mods/PZToolkitBridge/42/media/lua/client/PZToolkitBridge.lua"
    before = script.stat().st_mtime_ns
    press(app, "Connect to game")
    wait(app)
    assert script.stat().st_mtime_ns == before
    assert not (app.toolkit.profile / "backups").exists()


def test_first_connection_detects_and_saves_automatically(tk_root, tmp_path, monkeypatch):
    import pztoolkit.gui as gui
    monkeypatch.setattr(gui, "detect_folders", lambda current, data_dir: {"suggested": {"game_dir": str(tmp_path / "game"), "workspace_dir": str(tmp_path / "workspace"), "profile_dir": str(tmp_path / "profile")}})
    config = tmp_path / "settings/config.json"
    root = tk.Toplevel(tk_root)
    root.withdraw()
    application = Application(root, config)
    try:
        assert not config.exists()
        press(application, "Connect to game")
        assert wait(application)["ready"] is False
        assert config.exists()
        assert (tmp_path / "profile/.pztoolkit-profile").is_file()
        assert not (tmp_path / "workspace").exists()
    finally:
        application.close()


def test_ambiguous_discovery_does_not_write_config(tk_root, tmp_path, monkeypatch):
    import pztoolkit.gui as gui
    monkeypatch.setattr(gui, "detect_folders", lambda *args: {"suggested": {"game_dir": ""}, "notes": ["Multiple installations found"]})
    config = tmp_path / "missing.json"
    root = tk.Toplevel(tk_root)
    root.withdraw()
    application = Application(root, config)
    try:
        press(application, "Connect to game")
        assert "error" in wait(application)
        assert not config.exists()
        assert not application.connected
        assert "Ask Codex" in application.status.get()
    finally:
        application.close()


@pytest.mark.parametrize(("state", "message", "tone"), [
    ({"god_mode": True}, "God mode is on", "Status.TLabel"),
    ({"god_mode": False}, "God mode is off", "Status.TLabel"),
    ({"god_mode": False, "god_mode_error": "API failure"}, "god mode could not be enabled", "Warning.Status.TLabel"),
])
def test_connection_displays_actual_god_mode(app, monkeypatch, state, message, tone):
    monkeypatch.setattr(app.toolkit, "bridge_status", lambda: {"ready": True, **state})
    press(app, "Check connection")
    wait(app)
    assert app.connected
    assert message in app.status.get()
    assert app.status_label.cget("style") == tone
    assert "Game tools" in app.next_step.get()


def test_stale_connection_is_not_reported_as_connected(app):
    press(app, "Connect to game")
    wait(app)
    path = app.toolkit.profile / "Lua/pzt-status.txt"
    path.write_text(json.dumps({"ready": True, "timestamp_ms": (time.time() - 60) * 1000, "god_mode": True}))
    press(app, "Check connection")
    assert wait(app)["ready"] is False
    assert not app.connected
    assert "Not connected" in app.status.get()


@pytest.mark.parametrize(("identifier", "label", "description"), EDITORS)
def test_editor_buttons_use_shared_allowlisted_api(app, monkeypatch, identifier, label, description):
    calls = []
    monkeypatch.setattr(app.toolkit, "call", lambda name, arguments: calls.append((name, arguments)) or {"ok": True, "status": "passed", "message": "Requested editor"})
    press(app, label)
    wait(app)
    assert calls == [("editor_open", {"editor": identifier})]
    assert "requested" in app.status.get()
    assert "visibility is not verified" in app.status.get()


@pytest.mark.parametrize(("label", "enabled"), [("God mode on", True), ("God mode off", False)])
def test_god_mode_buttons_send_explicit_boolean(app, monkeypatch, label, enabled):
    calls = []
    monkeypatch.setattr(app.toolkit, "call", lambda name, arguments: calls.append((name, arguments)) or {"ok": True, "status": "passed", "message": "God mode changed"})
    press(app, label)
    wait(app)
    assert calls == [("god_mode", {"enabled": enabled})]


def test_inline_lua_requires_trust_and_has_no_scenario_file(app, monkeypatch):
    calls = []
    monkeypatch.setattr(app.toolkit, "call", lambda name, arguments: calls.append((name, arguments)) or {"ok": True, "status": "passed", "message": "fixture result"})
    press(app, "Run Lua command")
    assert not app.busy
    assert "trust checkbox" in app.status.get()
    app.trust_control.invoke()
    press(app, "Run Lua command")
    wait(app)
    assert calls == [("lua_execute", {"code": "return 'Hello from the game'\n"})]
    assert not app.toolkit.workspace.exists()
    assert "fixture result" in app.status.get()


def test_editing_lua_revokes_trust_and_preserves_text_across_navigation(app):
    app.trusted.set(True)
    app.editor.insert("end", "-- changed\n")
    app.root.update()
    assert not app.trusted.get()
    app.navigation["Connection"].invoke()
    app.navigation["Game tools"].invoke()
    assert "changed" in app.editor.get("1.0", "end")


def test_worker_serializes_actions_and_keeps_event_pump_alive(app, monkeypatch):
    calls = []
    def delayed(name, arguments):
        calls.append(name)
        time.sleep(0.15)
        return {"ready": False}
    monkeypatch.setattr(app.toolkit, "call", delayed)
    ticks = []
    app.root.after(1, lambda: ticks.append(1))
    press(app, "Check connection")
    assert all(str(button.cget("state")) == "disabled" for button in app.actions)
    assert app.editor.cget("state") == "disabled"
    app.dispatch("god_mode", {"enabled": True})
    app.close()
    assert app.root.winfo_exists()
    wait(app)
    assert calls == ["bridge_status"]
    assert ticks
    assert all(str(button.cget("state")) == "normal" for button in app.actions)
    assert app.root.tk.call("after", "info", app.poll_handle)


@pytest.mark.parametrize("outcome", [True, False, None])
def test_inline_game_transport_reports_pass_failure_and_unknown_without_workspace(app, outcome):
    press(app, "Connect to game")
    wait(app)
    lua = app.toolkit.profile / "Lua"
    (lua / "pzt-status.txt").write_text(json.dumps({"ready": True, "timestamp_ms": time.time() * 1000}))
    app.editor.delete("1.0", "end")
    app.editor.insert("1.0", "return 'inline test'")
    app.editor.edit_modified(False)
    app.root.update()
    app.trust_control.invoke()
    # Shorten only this transport wait, leaving the real core execution in place.
    original = app.toolkit.lua_execute
    def execute(code: str, timeout: float = 30) -> dict:
        return original(code, 0.25 if outcome is None else 2)
    app.toolkit.lua_execute = execute
    errors = []
    def respond():
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            request = lua / "pzt-request.txt"
            if request.exists() and len(request.read_text().splitlines()) >= 3:
                identifier = request.read_text().splitlines()[1]
                (lua / "pzt-response.txt").write_text(json.dumps({"id": identifier, "ok": outcome, "message": "fixture verdict"}))
                return
            time.sleep(0.01)
        errors.append("No request")
    responder = threading.Thread(target=respond) if outcome is not None else None
    if responder:
        responder.start()
    press(app, "Run Lua command")
    result = wait(app)
    if responder:
        responder.join(timeout=3)
    assert not errors
    assert result["status"] == ("passed" if outcome is True else "failed" if outcome is False else "timed_out")
    assert not app.toolkit.workspace.exists()
    assert not (app.toolkit.profile / "reports").exists()
    assert "unknown" in app.status.get() if outcome is None else "fixture verdict" in app.status.get()


def test_worker_error_is_readable_and_next_action_recovers(app, monkeypatch):
    monkeypatch.setattr(app.toolkit, "call", lambda *args: (_ for _ in ()).throw(ValueError("Load a world first")))
    press(app, "Check connection")
    assert "error" in wait(app)
    assert "Load a world first" in app.status.get()
    assert app.status_label.cget("style") == "Error.Status.TLabel"
    app.status.set("Trying again")
    assert app.status_label.cget("style") == "Status.TLabel"


def test_log_read_shows_plain_logs_in_details(app, monkeypatch):
    monkeypatch.setattr(app.toolkit, "call", lambda *args: {"exists": True, "lines": ["line one", "line two"]})
    press(app, "Read game logs")
    wait(app)
    assert app.details_open.get()
    assert app.output.get("1.0", "end-1c") == "line one\nline two"


def test_theme_has_legible_contrast_and_no_green(app):
    def luminance(color):
        channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        return sum(v * w for v, w in zip(values, (.2126, .7152, .0722)))
    style = ttk.Style(app.root)
    for name in ("TLabel", "Subtitle.TLabel", "TButton", "Accent.TButton", "Status.TLabel", "Error.Status.TLabel", "Warning.Status.TLabel"):
        foreground, background = (style.lookup(name, key) for key in ("foreground", "background"))
        dark, light = sorted((luminance(foreground), luminance(background)))
        assert (light + .05) / (dark + .05) >= 4.5
        for color in (foreground, background):
            red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            assert green <= max(red, blue)
    assert app.header_logo.width() > 0
    assert app.display_family == "Oxanium SemiBold"


def test_repeated_edit_trust_edit_always_revokes_trust(app):
    app.editor.insert("end", "-- first edit\n")
    app.root.update()
    app.trust_control.invoke()
    assert app.trusted.get()
    app.editor.insert("end", "-- second edit\n")
    app.root.update()
    assert not app.trusted.get()
    assert app.lua_dirty
    assert not app.editor.edit_modified()
    press(app, "Run Lua command")
    assert not app.busy
    assert "trust checkbox" in app.status.get()


def test_trusted_code_snapshot_blocks_edits_before_modified_event(app):
    app.trust_control.invoke()
    app.editor.insert("end", "-- changed without pumping events\n")
    press(app, "Run Lua command")
    assert not app.busy
    assert not app.trusted.get()
