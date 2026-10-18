"""Native game toolbelt. Every game action uses the shared CLI/MCP registry."""
import argparse
import json
import os
from pathlib import Path
import queue
import threading
import uuid
import tkinter as tk
from tkinter import messagebox, ttk

from .core import GAME_TOOL_NAMES, Toolkit, atomic_text
from .discovery import detect_folders

ASSETS = Path(__file__).parent / "assets/gui"
INK, PANEL, EDGE = "#141416", "#262326", "#414047"
TEXT, MUTED, ACCENT = "#f3eee4", "#c4bcb1", "#e5b26d"
EDITORS = (
    ("debug", "Open debug menu", "Open the game's built-in debug controls."),
    ("vehicle", "Vehicle editor", "Request the built-in vehicle editor in the game."),
    ("attachment", "Attachment editor", "Request the built-in model attachment editor."),
    ("animation", "Animation viewer", "Request the game's built-in animation viewer."),
    ("world_map", "World map editor", "Request the game's built-in world map editor."),
)


def default_config():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "PZToolkit/config.json"


class Application:
    def __init__(self, root, config):
        self.root, self.config = root, Path(config).resolve()
        self.toolkit = None
        self.busy = False
        self.last_result = None
        self.jobs = queue.Queue()
        self.actions = []
        self.connected = False
        self.lua_execution_available = None
        self.lua_dirty = False
        self.trusted_code = None
        self._style()
        root.title("Project Zomboid Toolkit")
        root.geometry("1280x960")
        root.minsize(1100, 860)
        root.configure(background=INK)
        root.protocol("WM_DELETE_WINDOW", self.close)
        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True)
        rail = ttk.Frame(outer, width=238, padding=18, style="Rail.TFrame")
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        logo = tk.PhotoImage(master=root, data=(ASSETS / "dead-signal-distressed.png").read_bytes(), format="png")
        self.header_logo = logo.subsample(max(1, (logo.width() + 199) // 200))
        self.icon = tk.PhotoImage(master=root, data=(ASSETS / "studio-icon.png").read_bytes(), format="png")
        root.iconphoto(True, self.icon)
        mark = tk.Canvas(rail, height=90, background=PANEL, highlightthickness=0)
        mark.pack(fill="x")
        mark.bind("<Configure>", lambda event: (mark.delete("all"), mark.create_image(event.width / 2, 42, image=self.header_logo)))
        ttk.Label(rail, text="Project Zomboid\nToolbelt", style="RailTitle.TLabel").pack(anchor="w", pady=(8, 24))
        shell = ttk.Frame(outer, padding=(24, 20))
        shell.pack(side="left", fill="both", expand=True)
        self.page_title = tk.StringVar(value="Connect to Project Zomboid")
        ttk.Label(shell, textvariable=self.page_title, style="Page.TLabel").pack(anchor="w", pady=(0, 14))
        self.status = tk.StringVar(value="Not checked yet. Click Connect to game to get started.")
        self.status_label = ttk.Label(shell, textvariable=self.status, style="Status.TLabel", padding=12, wraplength=800)
        self.status_label.pack(fill="x", pady=(0, 14))
        self.status_trace = self.status.trace_add("write", lambda *_: self.status_label.configure(style="Status.TLabel"))
        shell.bind("<Configure>", lambda event: self.status_label.configure(wraplength=max(350, event.width - 40)))
        self.tabs = ttk.Notebook(shell, style="Workspace.TNotebook")
        self.tabs.pack(fill="both", expand=True)
        self.connection = ttk.Frame(self.tabs, padding=16)
        self.tools = ttk.Frame(self.tabs, padding=16)
        self.navigation = {}
        for title, page in (("Connection", self.connection), ("Game tools", self.tools)):
            self.tabs.add(page, text=title)
            self.navigation[title] = ttk.Button(rail, text=title, style="Nav.TButton", command=lambda page=page: self.tabs.select(page))
            self.navigation[title].pack(fill="x", pady=4)
            page.bind("<Configure>", self.resize_page)
        ttk.Label(rail, text="Codex uses the same bridge.\nThis app need not stay open.", style="RailCopy.TLabel", wraplength=195).pack(side="bottom", anchor="w", pady=12)
        self.tabs.enable_traversal()
        self.tabs.bind("<<NotebookTabChanged>>", self.page_changed)
        self._connection_page()
        self._tools_page()
        footer = ttk.Frame(shell)
        footer.pack(fill="x", pady=(10, 0))
        self.details_open = tk.BooleanVar(value=False)
        ttk.Checkbutton(footer, text="Details (technical output)", variable=self.details_open, command=self.toggle_details).pack(anchor="w")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=140)
        self.details = ttk.Frame(footer)
        self.output = self.text_box(self.details, height=5)
        self.output.configure(state="disabled")
        self._load_existing()
        self.poll_handle = root.after(80, self.poll)

    def _style(self):
        self.display_family = "Segoe UI"
        if os.name == "nt":
            import ctypes
            register = ctypes.windll.gdi32.AddFontResourceExW
            register.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
            register.restype = ctypes.c_int
            if not register(str(ASSETS / "fonts/Oxanium-SemiBold.ttf"), 0x10, None):
                raise OSError("The bundled display font could not be loaded")
            self.display_family = "Oxanium SemiBold"
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 11), background=INK, foreground=TEXT, bordercolor=EDGE, focuscolor=ACCENT)
        style.configure("Page.TLabel", font=(self.display_family, 24))
        style.configure("Heading.TLabel", font=(self.display_family, 13))
        style.configure("Subtitle.TLabel", foreground=MUTED)
        style.configure("Rail.TFrame", background=PANEL)
        style.configure("RailTitle.TLabel", background=PANEL, font=(self.display_family, 17))
        style.configure("RailCopy.TLabel", background=PANEL, foreground=MUTED)
        style.configure("TButton", padding=(14, 10), background="#303035", foreground=TEXT, bordercolor=EDGE)
        style.map("TButton", background=[("disabled", "#252428"), ("pressed", "#4b454d"), ("active", "#414047")], foreground=[("disabled", "#a29aa3")])
        style.configure("Accent.TButton", background=ACCENT, foreground=INK)
        style.map("Accent.TButton", background=[("disabled", "#3b3035"), ("active", "#f4c68e")], foreground=[("disabled", "#b6a6ad"), ("active", INK)])
        style.configure("Nav.TButton", anchor="w", background=PANEL, foreground=MUTED, borderwidth=0, padding=(14, 13))
        style.configure("Selected.Nav.TButton", background="#733c32", foreground=TEXT)
        style.configure("Status.TLabel", background="#242328", foreground=TEXT)
        style.configure("Error.Status.TLabel", background="#321e20", foreground="#ffb0a5")
        style.configure("Warning.Status.TLabel", background="#342b22", foreground="#f3cf9e")
        style.layout("Workspace.TNotebook.Tab", [])
        style.configure("Workspace.TNotebook", borderwidth=0, background=INK)
        style.map("TCheckbutton", background=[("active", PANEL)], indicatorbackground=[("selected", ACCENT)])
        style.configure("TScrollbar", background=EDGE, troughcolor=INK, arrowcolor=TEXT)
        style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=PANEL)

    def button(self, parent, label, command, primary=False):
        button = ttk.Button(parent, text=label, command=command, style="Accent.TButton" if primary else "TButton")
        self.actions.append(button)
        return button

    @staticmethod
    def text_box(parent, height):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, height=height, wrap="word", font=("Consolas", 11), background="#1b1b1f", foreground=TEXT,
                       insertbackground=ACCENT, selectbackground="#733c32", selectforeground=TEXT,
                       highlightcolor=ACCENT, highlightbackground=EDGE, highlightthickness=1, relief="flat", padx=10, pady=10, undo=True)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        return text

    def _connection_page(self):
        if (ASSETS / "derelict-workshop.png").exists():
            self.hero_source = tk.PhotoImage(master=self.root, data=(ASSETS / "derelict-workshop.png").read_bytes(), format="png")
            self.hero_factor = None
            self.hero = tk.Canvas(self.connection, height=130, background=INK, highlightthickness=0)
            self.hero.pack(fill="x", pady=(0, 18))
            self.hero.bind("<Configure>", self.draw_hero)
        ttk.Label(self.connection, text="Connect Codex and this toolbelt to the game's debug tools and built-in editors.", wraplength=800, style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(self.connection, text="The bridge is a small game helper. Connect installs it only if needed, then checks the game. You do not need to create a mod or choose folders.", wraplength=800).pack(anchor="w", pady=(0, 16))
        self.next_step = tk.StringVar(value="Start here: Connect to game.")
        ttk.Label(self.connection, textvariable=self.next_step, wraplength=800).pack(anchor="w", pady=(0, 10))
        row = ttk.Frame(self.connection)
        row.pack(fill="x", pady=(0, 10))
        self.connect_button = self.button(row, "Connect to game", self.connect, True)
        self.connect_button.pack(side="left", padx=(0, 10))
        self.button(row, "Check connection", lambda: self.dispatch("bridge_status")).pack(side="left")
        self.launch_button = self.button(self.connection, "Launch Project Zomboid (test profile)", lambda: self.dispatch("game_launch"))
        self.launch_button.pack(anchor="w", pady=(0, 16))
        ttk.Label(self.connection, text="In the game: enable PZ Toolkit Bridge in Mods, enter a single-player world, and unpause. Then click Check connection. If that test game is already running, just connect to it.", wraplength=800).pack(anchor="w", pady=(0, 12))
        ttk.Label(self.connection, text="Launch opens the real game with debug enabled and separate test settings and saves. God mode turns on when your character loads with the bridge enabled.", wraplength=800, style="Subtitle.TLabel").pack(anchor="w", pady=(0, 12))
        ttk.Label(self.connection, text="Once connected, open Game tools to request the game's editors or change god mode. Codex can call these same tools through MCP without this window staying open.", wraplength=800, style="Subtitle.TLabel").pack(anchor="w")

    def _tools_page(self):
        ttk.Label(self.tools, text="Open the game's own tools", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.tools, text="Keep a debug single-player world loaded and unpaused. An editor can pause the game; return to the world and unpause before the next command.", wraplength=800).pack(anchor="w", pady=(6, 12))
        self.tool_tabs = ttk.Notebook(self.tools)
        self.tool_tabs.pack(fill="both", expand=True)
        self.editors_page = ttk.Frame(self.tool_tabs, padding=12)
        self.lua_page = ttk.Frame(self.tool_tabs, padding=12)
        self.tool_tabs.add(self.editors_page, text="Built-in editors")
        self.tool_tabs.add(self.lua_page, text="Lua command (advanced)")
        for index, (identifier, label, description) in enumerate(EDITORS):
            self.button(self.editors_page, label, lambda identifier=identifier: self.dispatch("editor_open", {"editor": identifier})).grid(row=index, column=0, sticky="ew", pady=5, padx=(0, 14))
            ttk.Label(self.editors_page, text=description, wraplength=450).grid(row=index, column=1, sticky="w", pady=5)
        self.editors_page.columnconfigure(1, weight=1)
        row = ttk.Frame(self.editors_page)
        row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(18, 10))
        self.button(row, "God mode on", lambda: self.dispatch("god_mode", {"enabled": True})).pack(side="left", padx=(0, 10))
        self.button(row, "God mode off", lambda: self.dispatch("god_mode", {"enabled": False})).pack(side="left")
        row = ttk.Frame(self.editors_page)
        row.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        self.button(row, "Read game logs", lambda: self.dispatch("logs_read")).pack(side="left", padx=(0, 10))
        self.button(row, "Check connection", lambda: self.dispatch("bridge_status")).pack(side="left")
        self.lua_help = tk.StringVar(value="Lua commands run directly in your loaded test world and may change it. Review the code before trusting it. No command files are needed.")
        ttk.Label(self.lua_page, textvariable=self.lua_help, wraplength=800).pack(anchor="w", pady=(0, 10))
        self.editor = self.text_box(self.lua_page, height=7)
        self.editor.insert("1.0", "return 'Hello from the game'\n")
        self.editor.edit_modified(False)
        self.trusted = tk.BooleanVar(value=False)
        self.editor.bind("<<Modified>>", self.editor_changed)
        self.trust_control = ttk.Checkbutton(self.lua_page, text="I reviewed this Lua and trust it to change my test world.", variable=self.trusted, command=self.confirm_trust)
        self.trust_control.pack(anchor="w", pady=10)
        self.lua_button = self.button(self.lua_page, "Run Lua command", self.run_lua, True)
        self.lua_button.pack(anchor="w")

    def draw_hero(self, event):
        factor = max(1, self.hero_source.width() // max(1, event.width))
        if factor != self.hero_factor:
            self.hero_image = self.hero_source.subsample(factor)
            self.hero_factor = factor
        self.hero.delete("all")
        self.hero.create_image(event.width / 2, 65, image=self.hero_image)

    @staticmethod
    def resize_page(event):
        def wrap(parent):
            for child in parent.winfo_children():
                if isinstance(child, ttk.Label) and int(child.cget("wraplength") or 0):
                    if not hasattr(child, "_wrap_limit"):
                        child._wrap_limit = int(child.cget("wraplength"))
                    child.configure(wraplength=max(300, min(child._wrap_limit, event.width - 45)))
                wrap(child)
        wrap(event.widget)

    def page_changed(self, event=None):
        selected = self.tabs.select()
        if not selected:
            return
        title = self.tabs.tab(selected, "text")
        self.page_title.set("Connect to Project Zomboid" if title == "Connection" else "Game tools")
        for name, button in self.navigation.items():
            button.configure(style="Selected.Nav.TButton" if name == title else "Nav.TButton")

    def toggle_details(self):
        if self.details_open.get():
            self.details.pack(fill="x", pady=(6, 0))
        else:
            self.details.pack_forget()

    def _load_existing(self):
        if self.config.exists():
            try:
                self.toolkit = Toolkit(self.config, tool_names=GAME_TOOL_NAMES)
            except (OSError, ValueError) as exc:
                self.display("Saved connection settings could not be loaded. Click Connect to game to retry; Details has the reason.", str(exc), "error")

    def _connect_operation(self):
        if not self.config.exists():
            detected = detect_folders({}, self.config.parent)
            data = detected["suggested"]
            if not data.get("game_dir"):
                raise ValueError("Could not identify one game installation. Ask Codex to repair the saved connection settings. " + " ".join(detected.get("notes", [])))
            self.config.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.config.with_name(self.config.name + "." + uuid.uuid4().hex + ".validate")
            try:
                atomic_text(temporary, json.dumps(data))
                Toolkit(temporary, tool_names=GAME_TOOL_NAMES)
                atomic_text(self.config, json.dumps(data, indent=2))
            finally:
                temporary.unlink(missing_ok=True)
        toolkit = Toolkit(self.config, tool_names=GAME_TOOL_NAMES)
        if not toolkit.call("doctor", {}).get("profile_prepared") or not (toolkit.profile / "mods/PZToolkitBridge/42/mod.info").is_file():
            toolkit.call("bridge_install", {})
        return toolkit, toolkit.call("bridge_status", {})

    def connect(self):
        self.start_job("connect", self._connect_operation)

    def dispatch(self, name, arguments=None):
        if self.busy:
            return
        if not self.toolkit:
            self.status.set("Click Connect to game first. It finds the saved game connection automatically.")
            self.tabs.select(self.connection)
            return
        toolkit = self.toolkit
        self.start_job(name, lambda: toolkit.call(name, arguments or {}))

    def editor_changed(self, event=None):
        if self.editor.edit_modified():
            self.lua_dirty = True
            self.trusted.set(False)
            self.trusted_code = None
            self.editor.edit_modified(False)

    def confirm_trust(self):
        self.trusted_code = self.editor.get("1.0", "end-1c") if self.trusted.get() else None

    def run_lua(self):
        if self.lua_execution_available is False:
            self.status.set("This game build cannot run custom Lua commands. God mode and built-in editors still work from Game tools.")
            return
        code = self.editor.get("1.0", "end-1c")
        if not self.trusted.get() or self.trusted_code != code:
            self.trusted.set(False)
            self.trusted_code = None
            self.status.set("Review the Lua, then select the trust checkbox before running it.")
            return
        if not code.strip() or len(code.encode("utf-8")) > 60 * 1024:
            self.status.set("Enter a Lua command no larger than 60 KiB, then review and trust it.")
            return
        self.dispatch("lua_execute", {"code": code})

    def display(self, summary, result, tone="info"):
        self.status.set(summary)
        self.status_label.configure(style={"error": "Error.Status.TLabel", "warning": "Warning.Status.TLabel"}.get(tone, "Status.TLabel"))
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result if isinstance(result, str) else json.dumps(result, indent=2, ensure_ascii=False))
        self.output.configure(state="disabled")

    def start_job(self, name, operation):
        if self.busy:
            return
        self.busy, self.last_result = True, None
        for button in self.actions:
            button.configure(state="disabled")
        self.editor.configure(state="disabled")
        self.trust_control.configure(state="disabled")
        self.progress.pack(anchor="e")
        self.progress.start(15)
        self.status.set("Waiting for the game to answer. Keep the world unpaused." if name in {"lua_execute", "god_mode", "editor_open"} else "Checking your game connection..." if name == "connect" else "Working. Please wait...")
        def worker():
            try:
                self.jobs.put((name, operation(), None))
            except Exception as exc:
                self.jobs.put((name, None, str(exc) or type(exc).__name__))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            self.deliver_job()
        finally:
            self.poll_handle = self.root.after(80, self.poll)

    def deliver_job(self):
        try:
            name, result, error = self.jobs.get_nowait()
        except queue.Empty:
            return
        self.busy = False
        self.progress.stop()
        self.progress.pack_forget()
        for button in self.actions:
            button.configure(state="normal")
        self.editor.configure(state="normal")
        self.trust_control.configure(state="normal")
        if name == "connect" and not error:
            self.toolkit, result = result
        self.last_result = {"error": error} if error else result
        tone, summary = "info", "Action completed."
        if error:
            if name in {"connect", "bridge_status"}:
                self.connected = False
                self.next_step.set("Connection check failed. Read the problem above, then Connect to game again.")
            tone = "error"
            summary = "Could not finish. " + error[:240] + " Open Details for the full reason."
        elif result.get("status") in {"timed_out", "invalid_response"}:
            tone = "warning"
            summary = "The game did not return a usable answer. The outcome is unknown. Unpause the world and check the connection before trying again."
        elif result.get("ok") is False:
            tone, summary = "error", "The game reported a problem. " + str(result.get("message", "Open Details for the reason."))
        elif name in {"connect", "bridge_status"}:
            self.connected = result.get("ready") is True
            self.lua_execution_available = result.get("lua_execution_available")
            self.lua_help.set("This game build does not support custom Lua commands. God mode and built-in editors still work in the Built-in editors tab." if self.lua_execution_available is False else "Lua commands run directly in your loaded test world and may change it. Review and trust the code before sending it. No command files are needed.")
            if self.connected:
                summary = "Connected to your game. " + ("God mode is on." if result.get("god_mode") is True else "God mode is off." if result.get("god_mode") is False else "God mode has not been reported.")
                if result.get("debug") is True:
                    summary += " Debug is on."
                elif result.get("debug") is False:
                    summary += " Debug is off."
                if result.get("single_player") is True:
                    summary += " Single-player world loaded."
                elif result.get("single_player") is False:
                    summary += " Multiplayer is not supported."
                if result.get("player_loaded") is False:
                    summary += " Player is not loaded."
                if result.get("god_mode_error"):
                    tone, summary = "warning", "Connected, but god mode could not be enabled. Open Details for the reason."
                self.next_step.set("Connected. Open Game tools to use the built-in editors or god mode buttons.")
            else:
                tone, summary = "warning", "Not connected. Launch the test game, enable PZ Toolkit Bridge, enter a single-player world and unpause. Then Check connection."
                self.next_step.set("Next: launch your test game, enter a world and unpause, then Check connection.")
            self.launch_button.configure(style="TButton" if self.connected else "Accent.TButton")
            self.connect_button.configure(style="TButton")
        elif name == "game_launch":
            self.connected = False
            summary = "Game launched. Enter a single-player world with PZ Toolkit Bridge enabled, unpause, then Check connection."
            self.next_step.set("Next: in the game, enter a world and unpause. Then Check connection.")
        elif name == "editor_open":
            summary = "Editor requested in the game. Switch to Project Zomboid to see it. Window visibility is not verified. Return to the world and unpause before another command."
        elif name == "god_mode":
            summary = str(result.get("message", "God mode command completed. Check connection to read the current state."))
        elif name == "lua_execute":
            summary = "Lua completed. " + str(result.get("message", "Open Details for the returned result."))
        elif name == "logs_read":
            summary = "Game logs loaded in Details." if result.get("exists") else "No game log yet. Launch the test game first, then Read game logs."
        self.lua_button.configure(state="disabled" if self.lua_execution_available is False else "normal")
        self.display(summary, error or ("\n".join(result["lines"]) if name == "logs_read" and not error else result), tone)
        if name == "logs_read" and not error and result.get("exists"):
            self.details_open.set(True)
            self.toggle_details()

    def close(self):
        if self.busy:
            self.status.set("Wait for the current action to finish. Closing cannot cancel Lua already running in the game.")
            return
        if self.lua_dirty and not messagebox.askyesno("Unsent Lua", "Close and discard the Lua text in this window?", parent=self.root):
            return
        self.root.after_cancel(self.poll_handle)
        self.status.trace_remove("write", self.status_trace)
        self.root.destroy()
        del self.header_logo, self.icon
        if hasattr(self, "hero_source"):
            del self.hero_source
        if hasattr(self, "hero_image"):
            del self.hero_image


def main():
    parser = argparse.ArgumentParser(description="Project Zomboid game toolbelt")
    parser.add_argument("--config", type=Path, default=default_config())
    parser.add_argument("--smoke-report", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = tk.Tk()
    app = Application(root, args.config)
    if args.smoke_report:
        import time
        root.geometry("1100x860")
        started = time.monotonic()
        def verify():
            if app.busy and time.monotonic() - started < 30:
                root.after(100, verify)
                return
            bounds = {}
            for label, page in (("connection", app.connection), ("tools", app.tools)):
                app.tabs.select(page)
                root.update_idletasks()
                buttons = [button for button in app.actions if str(button).startswith(str(page) + ".") and not str(button).startswith(str(app.lua_page) + ".")]
                bounds[label] = all(button.winfo_ismapped() and page.winfo_rootx() <= button.winfo_rootx() and button.winfo_rootx() + button.winfo_width() <= page.winfo_rootx() + page.winfo_width() and button.winfo_rooty() + button.winfo_height() <= page.winfo_rooty() + page.winfo_height() for button in buttons)
            app.tool_tabs.select(app.lua_page)
            root.update_idletasks()
            bounds["lua"] = app.trust_control.winfo_ismapped() and all(button.winfo_ismapped() for button in app.actions if str(button).startswith(str(app.lua_page) + "."))
            bridge = app.toolkit.profile / "mods/PZToolkitBridge" if app.toolkit else None
            result = {"ok": bool(app.last_result and "error" not in app.last_result), "window_mapped": bool(root.winfo_ismapped()), "bridge_assets": bool(bridge and (bridge / "42/media/lua/client/PZToolkitBridge.lua").is_file()), "branding_loaded": app.header_logo.width() > 0, "display_font": app.display_family, "tabs": [app.tabs.tab(page, "text") for page in app.tabs.tabs()], "navigation": list(app.navigation), "details_collapsed": not app.details_open.get(), "tools": list(app.toolkit.tools()) if app.toolkit else [], "bounds": bounds}
            atomic_text(args.smoke_report, json.dumps(result))
            app.close()
        root.after(150, app.connect)
        root.after(250, verify)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
