"""Real Tk widgets and simulated game responses, never the installed game."""

import json
import sys
import threading
import time

import pytest

tk = pytest.importorskip("tkinter")
from pztoolkit.gui import Application
from tkinter import ttk

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows GUI acceptance")


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(tmp_path, tk_root):
    root = tk.Toplevel(tk_root)
    root.withdraw()
    application = Application(root, tmp_path / "config.json")
    for key, name in (("game_dir", "game"), ("workspace_dir", "workspace"), ("profile_dir", "profile")):
        application.paths[key].set(str(tmp_path / name))
    application.save_setup()
    yield application
    application.editor.edit_modified(False)
    application.close()


def press(app, label):
    button = next(button for button in app.actions if button.cget("text") == label)
    button.invoke()


def wait(app):
    deadline = time.monotonic() + 5
    while app.busy and time.monotonic() < deadline:
        app.root.update()
        time.sleep(0.01)
    assert not app.busy, "GUI did not deliver background job result"
    return app.last_result


def create(app):
    app.mod_name.set("GuiExample")
    press(app, "Create mod")
    assert wait(app)["id"] == "GuiExample"


def test_create_check_deploy_from_widgets(app):
    press(app, "Prepare test profile")
    assert wait(app)["ok"]
    create(app)
    assert app.mod_list.selection() == ("mods/GuiExample",)
    press(app, "Check selected")
    assert wait(app)["ok"]
    press(app, "Deploy to test profile")
    result = wait(app)
    assert result["restart_required"]
    assert (app.toolkit.profile / "mods/GuiExample/42/mod.info").is_file()
    assert app.loaded_scenario == "scenarios/GuiExample_smoke.lua"


def test_unsaved_setup_blocks_old_profile_actions(app, tmp_path):
    app.paths["profile_dir"].set(str(tmp_path / "different-profile"))
    press(app, "Prepare test profile")
    assert not app.busy
    assert "Save setup" in app.status.get()
    assert not (tmp_path / "profile").exists()
    assert not (tmp_path / "different-profile").exists()
    press(app, "Save setup")
    press(app, "Prepare test profile")
    assert wait(app)["ok"]
    assert (tmp_path / "different-profile/.pztoolkit-profile").is_file()


def test_invalid_setup_preserves_saved_config(app):
    before = app.config.read_bytes()
    app.paths["profile_dir"].set(str(app.toolkit.game / "overlap"))
    press(app, "Save setup")
    assert app.config.read_bytes() == before
    assert "not saved" in app.status.get()


def test_background_create_locks_setup_and_keeps_event_pump_alive(app, tmp_path):
    app.mod_name.set("GuiExample")
    press(app, "Create mod")
    assert all(str(entry.cget("state")) == "disabled" for entry in app.path_entries)
    # A programmatic config change must not break result delivery either.
    app.paths["profile_dir"].set(str(tmp_path / "new-profile"))
    assert wait(app)["id"] == "GuiExample"
    assert all(str(entry.cget("state")) == "normal" for entry in app.path_entries)
    assert app.root.tk.call("after", "info", app.poll_handle)


def test_editor_save_and_trust_gate(app):
    create(app)
    app.editor.insert("end", "\nreturn 'edited'\n")
    press(app, "Run saved scenario")
    assert not app.busy
    assert "Save your scenario" in app.status.get()
    press(app, "Save scenario")
    assert "edited" in (app.toolkit.workspace / app.loaded_scenario).read_text()
    press(app, "Run saved scenario")
    assert not app.busy
    assert "trust checkbox" in app.status.get()


def test_discarded_editor_never_overwrites_new_workspace(app, tmp_path, monkeypatch):
    create(app)
    app.editor.insert("end", "\n-- old unsaved text\n")
    other = tmp_path / "other"
    scenario = other / "scenarios/GuiExample_smoke.lua"
    scenario.parent.mkdir(parents=True)
    scenario.write_text("return 'other workspace'\n")
    config = tmp_path / "other.json"
    config.write_text(json.dumps({"game_dir": "game", "workspace_dir": "other", "profile_dir": "other-profile"}))
    prompts = []
    monkeypatch.setattr("pztoolkit.gui.messagebox.askyesnocancel", lambda *a, **k: prompts.append(1) or False)
    app.load_config(config)
    assert prompts == [1]
    assert scenario.read_text() == "return 'other workspace'\n"
    assert "other workspace" in app.editor.get("1.0", "end")
    assert not app.trusted.get()
    assert str(config) in app.config_note.get()


@pytest.mark.parametrize("outcome", [True, False, None])
def test_test_run_keeps_ui_responsive_and_reports_outcomes(app, outcome):
    press(app, "Prepare test profile")
    wait(app)
    create(app)
    lua = app.toolkit.profile / "Lua"
    (lua / "pzt-status.txt").write_text(json.dumps({"ready": True, "timestamp_ms": time.time() * 1000, "build": "fixture"}))
    app.trusted.set(True)
    app.timeout.set("0.2" if outcome is None else "2")
    responder_errors = []

    def respond():
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            request = lua / "pzt-request.txt"
            if request.exists() and len(request.read_text().splitlines()) >= 3:
                identifier = request.read_text().splitlines()[1]
                (lua / "pzt-response.txt").write_text(json.dumps({"id": identifier, "ok": outcome, "message": "fixture verdict"}))
                return
            time.sleep(0.01)
        responder_errors.append("No request")

    responder = None
    if outcome is not None:
        responder = threading.Thread(target=respond)
        responder.start()
    ticks = []
    app.root.after(1, lambda: ticks.append(1))
    press(app, "Run saved scenario")
    assert app.busy
    assert str(app.run_button.cget("state")) == "disabled"
    app.close()
    assert app.root.winfo_exists()
    result = wait(app)
    if responder:
        responder.join(timeout=3)
    assert not responder_errors
    assert ticks, "GUI event loop blocked during the harness wait"
    assert result["status"] == ("passed" if outcome is True else "failed" if outcome is False else "timed_out")
    assert list((app.toolkit.profile / "reports").glob("*.json"))
    assert "unknown" in app.status.get() if outcome is None else "fixture verdict" in app.output.get("1.0", "end")


def test_scenario_path_escape_is_visible_error(app):
    app.scenario.set("../outside.lua")
    app.load_scenario()
    assert app.loaded_scenario is None
    assert "Could not load" in app.status.get()
    assert "escapes" in app.output.get("1.0", "end")


def test_theme_keeps_reading_and_action_surfaces_legible(app):
    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    style = ttk.Style(app.root)
    for name in ("TLabel", "Subtitle.TLabel", "TButton", "Accent.TButton", "Status.TLabel", "Error.Status.TLabel", "Warning.Status.TLabel"):
        values = sorted((luminance(style.lookup(name, "foreground")), luminance(style.lookup(name, "background"))))
        assert (values[1] + 0.05) / (values[0] + 0.05) >= 4.5, name
    assert app.header_logo.width() > 0 and app.header_art.width() > 0
    assert app.display_family == "Oxanium SemiBold"


def test_result_tone_resets_when_next_action_changes_status(app):
    app.display("Action failed.", "fixture", "error")
    assert app.status_label.cget("style") == "Error.Status.TLabel"
    app.status.set("Setup saved.")
    assert app.status_label.cget("style") == "Status.TLabel"
