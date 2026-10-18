"""Native desktop adapter for the shared toolkit, with serialized background jobs."""

import argparse
import json
import os
from pathlib import Path
import queue
import threading
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import Toolkit, atomic_text, confined, linked
from .discovery import detect_folders

ASSETS = Path(__file__).parent / "assets/gui"
INK = "#141416"
PANEL = "#1e1e22"
EDGE = "#414047"
TEXT = "#f1edef"
MUTED = "#bcb5bc"
ACCENT = "#ef8b82"

GUIDE = (
    ("Setup", "Save setup", "save_setup", "Choose your folders", "Use Detect folders or Browse, review your game installation, mod workspace and separate test profile, then save setup."),
    ("Setup", "Prepare test profile", "profile_prepare", "Prepare the isolated profile", "Install the toolkit bridge into the separate test profile. Your normal saves and mods stay outside it."),
    ("Mods", "Create mod", "mod_create", "Create a development mod", "Enter a new mod ID, then create it. A matching Lua smoke scenario is generated for you."),
    ("Mods", "Check selected", "mod_check", "Check your mod", "Select a mod in the list, then check its folder layout and metadata."),
    ("Mods", "Deploy to test profile", "mod_deploy", "Deploy your changes", "Copy the checked mod into the isolated profile. Previous deployments are backed up."),
    ("In-game tests", "Launch Project Zomboid (test profile)", "game_launch", "Open Project Zomboid", "Launch Project Zomboid with the isolated test profile. Enable PZ Toolkit Bridge and your mod, load a disposable single-player world and unpause it."),
    ("In-game tests", "Check bridge", "bridge_status", "Wait for the game bridge", "Keep the test world loaded and unpaused, then check that the bridge is ready."),
    ("In-game tests", "Run saved scenario", "harness_run", "Run your first test", "Review the scenario, save any edits, select the trust checkbox and run. Results appear in the activity dock."),
)


def default_config() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "PZToolkit/config.json"


class Application:
    def __init__(self, root: tk.Tk, config: Path, *, autodetect=True):
        self.root, self.config = root, Path(config).resolve()
        self.toolkit = None
        self.saved_paths = {}
        self.busy = False
        self.last_result = None
        self.jobs = queue.Queue()
        self.actions = []
        self.path_entries = []
        self.path_traces = []
        self.loaded_scenario = None
        self.guide_index = 0
        self.guide_complete = False
        self.guide_enabled = tk.BooleanVar(master=root, value=True)
        self.guide_arrow = None
        self.guide_target = None
        self.guide_original_style = None
        root.title("Project Zomboid Toolkit")
        root.geometry("1280x960")
        root.minsize(1100, 860)
        root.configure(background=INK)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._style()
        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True)
        sidebar = ttk.Frame(outer, width=238, padding=(18, 18), style="Rail.TFrame")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._header(sidebar)
        shell = ttk.Frame(outer, padding=(24, 20))
        shell.pack(side="left", fill="both", expand=True)
        self.page_title = tk.StringVar(value="Setup")
        self.page_caption = tk.StringVar(value="Choose your development environment.")
        ttk.Label(shell, textvariable=self.page_title, style="Page.TLabel").pack(anchor="w")
        ttk.Label(shell, textvariable=self.page_caption, style="Subtitle.TLabel").pack(anchor="w", pady=(4, 16))
        self.guide_bar = ttk.Frame(shell, padding=12, style="Guide.TFrame")
        self.guide_bar.pack(fill="x", pady=(0, 10))
        self.guide_title = tk.StringVar()
        self.guide_copy = tk.StringVar()
        guide_top = ttk.Frame(self.guide_bar, style="Guide.TFrame")
        guide_top.pack(fill="x")
        ttk.Label(guide_top, textvariable=self.guide_title, style="GuideTitle.TLabel").pack(side="left")
        self.guide_next = ttk.Button(guide_top, text="Next", command=lambda: self.show_guide(self.guide_index + 1))
        self.guide_next.pack(side="right")
        self.guide_previous = ttk.Button(guide_top, text="Previous", command=lambda: self.show_guide(self.guide_index - 1))
        self.guide_previous.pack(side="right", padx=6)
        self.guide_show = ttk.Button(guide_top, text="Show me", command=lambda: self.show_guide(self.guide_index))
        self.guide_show.pack(side="right", padx=(0, 6))
        self.guide_description = ttk.Label(self.guide_bar, textvariable=self.guide_copy, wraplength=800, style="GuideCopy.TLabel")
        self.guide_description.pack(fill="x", pady=(8, 0))
        self.status = tk.StringVar(value="Start with Setup: choose your game and development folders.")
        self.status_label = ttk.Label(shell, textvariable=self.status, style="Status.TLabel", wraplength=1090,
                                      padding=12)
        self.status_label.pack(fill="x", pady=(0, 12))
        self.status_trace = self.status.trace_add("write", lambda *_: self.status_label.configure(style="Status.TLabel"))
        shell.bind("<Configure>", self.resize_content)
        self.panes = ttk.Panedwindow(shell, orient="vertical")
        self.panes.pack(fill="both", expand=True)
        self.tabs = ttk.Notebook(self.panes, style="Workspace.TNotebook")
        self.panes.add(self.tabs, weight=4)
        self.setup = ttk.Frame(self.tabs, padding=18)
        self.mods = ttk.Frame(self.tabs, padding=18)
        self.tests = ttk.Frame(self.tabs, padding=18)
        for page, title in ((self.setup, "Setup"), (self.mods, "Mods"), (self.tests, "In-game tests")):
            self.tabs.add(page, text=title)
            page.bind("<Configure>", self.resize_page)
        self.navigation = {}
        for title, page in (("Mods", self.mods), ("In-game tests", self.tests), ("Setup", self.setup)):
            button = ttk.Button(sidebar, text=title, command=lambda page=page: self.tabs.select(page), style="Nav.TButton")
            button.pack(fill="x", pady=4)
            self.navigation[title] = button
        ttk.Checkbutton(sidebar, text="Show guide", variable=self.guide_enabled, command=self.toggle_guide,
                        style="Rail.TCheckbutton").pack(anchor="w", pady=(22, 0))
        ttk.Label(sidebar, text="Local mod development\nCLI and MCP included", style="RailCopy.TLabel",
                  justify="left").pack(side="bottom", anchor="w", pady=10)
        self.tabs.enable_traversal()
        self.tabs.bind("<<NotebookTabChanged>>", self.page_changed)
        self._setup_page()
        self._mods_page()
        self._tests_page()
        activity = ttk.Frame(self.panes, padding=(0, 12, 0, 0))
        self.panes.add(activity, weight=1)
        footer = ttk.Frame(activity)
        footer.pack(fill="x", pady=(0, 8))
        ttk.Label(footer, text="Activity & results", style="Heading.TLabel").pack(side="left")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=140)
        self.output = self.text_box(activity, height=6, readonly=True)
        self.output.insert("1.0", "Tool results and game logs appear here. Your normal saves and mods stay outside the test profile.")
        self.output.configure(state="disabled")
        self.load_config(self.config)
        self.show_guide(0)
        self.poll_handle = root.after(80, self.poll)
        if autodetect and not self.config.exists():
            root.after_idle(self.detect_folders)

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
        style.configure(".", font=("Segoe UI", 10), background=INK, foreground=TEXT,
                        bordercolor=EDGE, lightcolor=EDGE, darkcolor=INK, focuscolor=ACCENT)
        style.configure("Page.TLabel", font=(self.display_family, 24))
        style.configure("Rail.TFrame", background=PANEL)
        style.configure("RailTitle.TLabel", background=PANEL, font=(self.display_family, 17))
        style.configure("RailCopy.TLabel", background=PANEL, foreground=MUTED)
        style.configure("Rail.TCheckbutton", background=PANEL)
        style.configure("Nav.TButton", anchor="w", background=PANEL, foreground=MUTED,
                        padding=(14, 13), borderwidth=0, relief="flat")
        style.map("Nav.TButton", background=[("active", "#303034")], foreground=[("active", TEXT)])
        style.configure("Selected.Nav.TButton", background="#462c32", foreground=TEXT)
        style.map("Selected.Nav.TButton", background=[("active", "#56353b")], foreground=[("active", TEXT)])
        style.configure("Guide.TFrame", background="#28252a")
        style.configure("GuideTitle.TLabel", background="#28252a", font=("Segoe UI", 10, "bold"))
        style.configure("GuideCopy.TLabel", background="#28252a", foreground=MUTED)
        style.configure("Subtitle.TLabel", foreground=MUTED)
        style.configure("Heading.TLabel", font=(self.display_family, 12))
        style.configure("Status.TLabel", background="#242328", foreground=TEXT)
        style.configure("Error.Status.TLabel", background="#321e20", foreground="#ffb0a5")
        style.configure("Warning.Status.TLabel", background="#342b22", foreground="#f3cf9e")
        style.configure("TButton", padding=(14, 9), background="#303035", foreground=TEXT,
                        bordercolor="#55515a", focuscolor=ACCENT)
        style.map("TButton", background=[("disabled", "#252428"), ("pressed", "#4b454d"), ("active", "#414047")],
                  foreground=[("disabled", "#a29aa3")])
        style.configure("Accent.TButton", background=ACCENT, foreground=INK, bordercolor=ACCENT)
        style.map("Accent.TButton", background=[("disabled", "#3b3035"), ("pressed", "#da746e"), ("active", "#ffa69b")],
                  foreground=[("disabled", "#b6a6ad"), ("active", INK)])
        style.configure("Guide.TButton", background="#502b32", foreground=TEXT, bordercolor=ACCENT, padding=(24, 9))
        style.map("Guide.TButton", background=[("disabled", "#34282d"), ("active", "#663640")],
                  foreground=[("disabled", "#b6a6ad"), ("active", TEXT)])
        style.configure("TNotebook", background=INK, bordercolor=EDGE, tabmargins=(0, 0, 0, 0))
        style.layout("Workspace.TNotebook.Tab", [])
        style.configure("Workspace.TNotebook", borderwidth=0)
        style.configure("Treeview", rowheight=36, background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, bordercolor=EDGE)
        style.map("Treeview", background=[("selected", "#57333b")], foreground=[("selected", TEXT)])
        style.configure("Treeview.Heading", padding=9, background="#2b292e", foreground=TEXT,
                        font=(self.display_family, 10), relief="flat")
        style.map("Treeview.Heading", background=[("active", "#39353c")])
        for control in ("TEntry", "TSpinbox", "TCombobox"):
            style.configure(control, fieldbackground="#1b1b1f", foreground=TEXT, padding=6,
                            insertcolor=ACCENT, selectbackground="#57333b", selectforeground=TEXT,
                            arrowcolor=TEXT, bordercolor=EDGE)
            style.map(control, fieldbackground=[("disabled", "#242328"), ("readonly", "#1b1b1f")],
                      foreground=[("disabled", "#a29aa3"), ("readonly", TEXT)],
                      bordercolor=[("focus", ACCENT)])
        style.map("TCheckbutton", background=[("active", "#2a272c")], indicatorbackground=[("selected", ACCENT)])
        style.configure("TScrollbar", background="#48414b", troughcolor=INK, arrowcolor=TEXT, bordercolor=EDGE)
        style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=PANEL, bordercolor=EDGE)
        self.root.option_add("*TCombobox*Listbox.background", "#1b1b1f")
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#57333b")
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEXT)

    def _header(self, parent):
        self.header = tk.Canvas(parent, height=86, background=PANEL, highlightthickness=0)
        self.header.pack(fill="x")
        original_logo = tk.PhotoImage(master=self.root, data=(ASSETS / "dead-signal-distressed.png").read_bytes(), format="png")
        self.header_logo = original_logo.subsample(max(1, (original_logo.width() + 199) // 200))
        self.icon = tk.PhotoImage(master=self.root, data=(ASSETS / "studio-icon.png").read_bytes(), format="png")
        self.root.iconphoto(True, self.icon)
        self.header.bind("<Configure>", self.draw_header)
        ttk.Label(parent, text="Project Zomboid\nToolkit", style="RailTitle.TLabel", justify="left").pack(anchor="w", pady=(8, 28))

    def draw_header(self, event):
        canvas = self.header
        canvas.delete("all")
        canvas.create_image(event.width / 2, 40, image=self.header_logo, anchor="center")

    def resize_content(self, event):
        self.status_label.configure(wraplength=max(400, event.width - 30))
        self.guide_description.configure(wraplength=max(360, event.width - 60))

    @staticmethod
    def resize_page(event):
        def wrap(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.Label) and int(widget.cget("wraplength") or 0):
                    widget.configure(wraplength=max(300, event.width - 45))
                wrap(widget)
        wrap(event.widget)

    def page_changed(self, event=None):
        selected = self.tabs.select()
        if not selected:
            return
        title = self.tabs.tab(selected, "text")
        self.page_title.set(title)
        self.page_caption.set({"Setup": "Choose your development environment.",
                               "Mods": "Create, check and deploy your workspace mods.",
                               "In-game tests": "Run saved Lua scenarios and inspect the game evidence."}[title])
        for name, button in self.navigation.items():
            button.configure(style="Selected.Nav.TButton" if name == title else "Nav.TButton")
        self.point_guide()

    def clear_guide_arrow(self):
        if self.guide_arrow is not None:
            self.guide_arrow.destroy()
            self.guide_arrow = None
        if self.guide_target is not None:
            self.guide_target.configure(style=self.guide_original_style)
            self.guide_target = None

    def point_guide(self):
        self.clear_guide_arrow()
        if not self.guide_enabled.get() or self.busy or self.guide_complete:
            return
        page, label, _, _, _ = GUIDE[self.guide_index]
        if self.tabs.tab(self.tabs.select(), "text") != page:
            return
        target = next((button for button in self.actions if button.cget("text") == label), None)
        if target is None:
            return
        self.guide_target = target
        self.guide_original_style = target.cget("style")
        target.configure(style="Guide.TButton")
        self.guide_arrow = tk.Canvas(target, width=15, height=16, highlightthickness=0, background="#502b32")
        self.guide_arrow.create_line(1, 8, 13, 8, arrow="last", fill=ACCENT, width=2)
        self.guide_arrow.place(x=4, rely=0.5, anchor="w")
        self.guide_arrow.bind("<Button-1>", lambda event: target.invoke())

    def show_guide(self, index):
        if self.busy:
            return
        self.guide_index = max(0, min(len(GUIDE) - 1, index))
        self.guide_complete = False
        page, _, _, title, description = GUIDE[self.guide_index]
        self.guide_title.set(f"{self.guide_index + 1} of {len(GUIDE)}: {title}")
        self.guide_copy.set(description)
        self.guide_previous.configure(state="disabled" if self.guide_index == 0 else "normal")
        self.guide_next.configure(state="disabled" if self.guide_index == len(GUIDE) - 1 else "normal")
        if self.guide_enabled.get():
            self.tabs.select({"Setup": self.setup, "Mods": self.mods, "In-game tests": self.tests}[page])
        self.point_guide()

    def toggle_guide(self):
        if self.guide_enabled.get():
            self.guide_bar.pack(fill="x", pady=(0, 10), before=self.status_label)
            self.show_guide(self.guide_index)
        else:
            self.guide_bar.pack_forget()
            self.clear_guide_arrow()

    def advance_guide(self, action):
        if not self.guide_enabled.get() or GUIDE[self.guide_index][2] != action:
            return
        if self.guide_index < len(GUIDE) - 1:
            self.show_guide(self.guide_index + 1)
        else:
            self.guide_complete = True
            self.clear_guide_arrow()
            self.guide_copy.set("The game returned a passing result. Inspect the report below, edit your mod and scenario, then deploy and test again.")

    def button(self, parent, label, command, primary=False):
        button = ttk.Button(parent, text=label, command=command,
                            style="Accent.TButton" if primary else "TButton")
        button.pack(side="left", padx=(0, 8))
        self.actions.append(button)
        return button

    @staticmethod
    def text_box(parent, height, readonly=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, height=height, wrap="word", font=("Consolas", 10),
                       background="#1b1b1f", foreground=TEXT, insertbackground=ACCENT,
                       selectbackground="#57333b", selectforeground=TEXT, highlightcolor=ACCENT,
                       highlightbackground=EDGE, highlightthickness=1, relief="flat", borderwidth=0,
                       padx=10, pady=10, undo=not readonly)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        return text

    def _setup_page(self):
        ttk.Label(self.setup, text="Your development environment", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self.setup, text="Choose separate game, workspace and test profile folders. Game files are read-only.",
                  wraplength=900).pack(anchor="w", pady=(6, 10))
        self.paths = {}
        data = self.config.parent
        defaults = {"game_dir": "C:/Games/ProjectZomboid", "workspace_dir": str(data / "workspace"),
                    "profile_dir": str(data / "game-profile")}
        for key, label in (("game_dir", "Project Zomboid installation"),
                           ("workspace_dir", "Mod workspace"), ("profile_dir", "Isolated test profile")):
            ttk.Label(self.setup, text=label).pack(anchor="w", pady=(8, 3))
            row = ttk.Frame(self.setup)
            row.pack(fill="x")
            value = tk.StringVar(value=defaults[key])
            self.paths[key] = value
            self.path_traces.append((value, value.trace_add("write", self.settings_changed)))
            entry = ttk.Entry(row, textvariable=value)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.path_entries.append(entry)
            self.button(row, "Browse…", lambda key=key: self.browse_directory(key))
        self.config_note = tk.StringVar(value=f"Settings: {self.config}")
        ttk.Label(self.setup, textvariable=self.config_note, wraplength=900,
                  style="Subtitle.TLabel").pack(anchor="w", pady=(10, 12))
        row = ttk.Frame(self.setup)
        row.pack(fill="x")
        self.button(row, "Detect folders", self.detect_folders)
        self.button(row, "Save setup", self.save_setup, True)
        self.button(row, "Open config…", self.choose_config)
        self.button(row, "Check installation", lambda: self.dispatch("doctor"))
        self.button(row, "Prepare test profile", lambda: self.dispatch("profile_prepare"))

    def _mods_page(self):
        ttk.Label(self.mods, text="Development mods", style="Heading.TLabel").pack(anchor="w")
        self.mod_hint = tk.StringVar(value="Save your setup to load the workspace.")
        ttk.Label(self.mods, textvariable=self.mod_hint, style="Subtitle.TLabel",
                  wraplength=900).pack(anchor="w", pady=(6, 10))
        row = ttk.Frame(self.mods)
        row.pack(fill="x", pady=(0, 10))
        self.mod_name = tk.StringVar()
        ttk.Label(row, text="New mod ID").pack(side="left", padx=(0, 8))
        ttk.Entry(row, textvariable=self.mod_name, width=28).pack(side="left", padx=(0, 8))
        self.button(row, "Create mod", self.create_mod, True)
        self.button(row, "Refresh", self.refresh_mods)
        self.mod_list = ttk.Treeview(self.mods, columns=("path",), selectmode="browse", height=5)
        self.mod_list.heading("#0", text="Mod folder", anchor="w")
        self.mod_list.heading("path", text="Workspace path", anchor="w")
        self.mod_list.column("#0", width=240)
        self.mod_list.column("path", width=440)
        footer = ttk.Frame(self.mods)
        footer.pack(side="bottom", fill="x", pady=(12, 0))
        row = ttk.Frame(footer)
        row.pack(fill="x")
        self.button(row, "Check selected", lambda: self.selected_mod("mod_check"))
        self.button(row, "Deploy to test profile", lambda: self.selected_mod("mod_deploy"), True)
        self.button(row, "Open mod folder", self.open_mod)
        ttk.Label(footer, text="Deployment keeps a backup of the previous copy. Reload the test world after changes.",
                  wraplength=900).pack(anchor="w", pady=(10, 0))
        self.mod_list.pack(fill="both", expand=True)

    def _tests_page(self):
        row = ttk.Frame(self.tests)
        row.pack(fill="x", pady=(0, 8))
        self.button(row, "Launch Project Zomboid (test profile)", lambda: self.dispatch("game_launch"))
        row = ttk.Frame(self.tests)
        row.pack(fill="x", pady=(0, 8))
        self.button(row, "Check bridge", lambda: self.dispatch("bridge_status"))
        self.button(row, "Read game logs", lambda: self.dispatch("logs_read"))
        self.button(row, "Open reports", self.open_reports)
        ttk.Label(self.tests, text="Enable PZ Toolkit Bridge and your mod in the isolated game. Load a disposable single-player world and unpause it.",
                  wraplength=900).pack(anchor="w", pady=(0, 10))
        row = ttk.Frame(self.tests)
        row.pack(fill="x", pady=(0, 8))
        ttk.Label(row, text="Scenario").pack(side="left", padx=(0, 8))
        self.scenario = tk.StringVar()
        self.scenarios = ttk.Combobox(row, textvariable=self.scenario, state="readonly", width=48)
        self.scenarios.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.scenarios.bind("<<ComboboxSelected>>", self.load_scenario)
        self.button(row, "Refresh scenarios", self.refresh_scenarios)
        self.editor = self.text_box(self.tests, height=6)
        self.editor.bind("<<Modified>>", self.editor_changed)
        self.scenario_note = tk.StringVar(value="Create a mod to generate a matching smoke scenario.")
        ttk.Label(self.tests, textvariable=self.scenario_note, style="Subtitle.TLabel").pack(anchor="w", pady=5)
        row = ttk.Frame(self.tests)
        row.pack(fill="x")
        self.button(row, "Save scenario", self.save_scenario)
        ttk.Label(row, text="Timeout (seconds)").pack(side="left", padx=(8, 6))
        self.timeout = tk.StringVar(value="30")
        ttk.Spinbox(row, from_=1, to=300, textvariable=self.timeout, width=5).pack(side="left", padx=(0, 10))
        self.run_button = self.button(row, "Run saved scenario", self.run_scenario, True)
        self.trusted = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.tests, text="I trust this Lua scenario to run in my disposable game world.",
                        variable=self.trusted).pack(anchor="w", pady=(8, 0))

    def display(self, summary, result, tone="info"):
        self.status.set(summary)
        self.status_label.configure(style={"error": "Error.Status.TLabel", "warning": "Warning.Status.TLabel"}.get(tone, "Status.TLabel"))
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result if isinstance(result, str) else json.dumps(result, indent=2, ensure_ascii=False))
        self.output.configure(state="disabled")

    def browse_directory(self, key):
        directory = filedialog.askdirectory(parent=self.root, title="Choose folder", mustexist=False)
        if directory:
            self.paths[key].set(directory)

    def choose_config(self):
        path = filedialog.askopenfilename(parent=self.root, title="Open toolkit configuration", filetypes=[("JSON", "*.json")])
        if path:
            self.load_config(Path(path))

    def detect_folders(self):
        current = {key: value.get().strip() for key, value in self.paths.items()}
        data_dir = self.config.parent

        def detected(result):
            for key, value in result["suggested"].items():
                if value:
                    self.paths[key].set(value)
            found = result["suggested"].get("game_dir")
            self.display("Folders detected. Review the paths, then Save setup." if found else
                         "Choose a game folder using Browse. See detection details below.", result,
                         "info" if found else "warning")
            self.tabs.select(self.setup)

        self.start_job("folders_detect", lambda: detect_folders(current, data_dir), detected)

    def load_config(self, path):
        if not path.exists():
            return
        try:
            toolkit = Toolkit(path)
            if not self.discard_changes():
                return
            self.loaded_scenario = None
            self.editor.delete("1.0", "end")
            self.editor.edit_modified(False)
            self.trusted.set(False)
            self.config, self.toolkit = path.resolve(), toolkit
            self.config_note.set(f"Settings: {self.config}")
            for key, value in (("game_dir", toolkit.game), ("workspace_dir", toolkit.workspace), ("profile_dir", toolkit.profile)):
                self.paths[key].set(str(value))
            self.saved_paths = {key: value.get() for key, value in self.paths.items()}
            self.refresh_mods()
            self.refresh_scenarios()
            self.tabs.select(self.mods)
            self.status.set("Setup loaded. Select a mod, or create your first development mod.")
        except (OSError, ValueError) as exc:
            self.display("Setup needs attention.", str(exc), "error")
            self.tabs.select(self.setup)

    def save_setup(self):
        if not self.discard_changes():
            return
        temporary = self.config.with_name(self.config.name + f".{uuid.uuid4().hex}.validate")
        try:
            self.config.parent.mkdir(parents=True, exist_ok=True)
            data = {key: value.get().strip() for key, value in self.paths.items()}
            atomic_text(temporary, json.dumps(data, indent=2))
            Toolkit(temporary)  # Validate isolation before replacing an existing configuration.
            atomic_text(self.config, json.dumps(data, indent=2))
            self.load_config(self.config)
            self.status.set("Setup saved. Prepare the test profile before deploying or launching.")
            self.advance_guide("save_setup")
        except (OSError, ValueError) as exc:
            self.display("Setup was not saved.", str(exc), "error")
        finally:
            temporary.unlink(missing_ok=True)

    def refresh_mods(self):
        if not self.ready():
            return
        self.mod_list.delete(*self.mod_list.get_children())
        try:
            folder = confined(self.toolkit.workspace, "mods")
            for path in sorted(folder.iterdir()) if folder.exists() else []:
                if path.is_dir() and not linked(path):
                    relative = path.relative_to(self.toolkit.workspace).as_posix()
                    self.mod_list.insert("", "end", iid=relative, text=path.name, values=(relative,))
            count = len(self.mod_list.get_children())
            self.mod_hint.set(f"{count} development mod(s) in {self.toolkit.workspace}" if count else
                              "No development mods yet. Enter a mod ID and choose Create mod.")
        except (OSError, ValueError) as exc:
            self.display("Could not read the workspace.", str(exc), "error")

    def create_mod(self):
        def created(result):
            self.refresh_mods()
            if self.mod_list.exists(result["mod"]):
                self.mod_list.selection_set(result["mod"])
            self.refresh_scenarios()
        self.dispatch("mod_create", {"name": self.mod_name.get().strip()}, created)

    def selected_mod(self, tool):
        selection = self.mod_list.selection()
        if not selection:
            self.status.set("Select a development mod first.")
            return
        self.dispatch(tool, {"mod": selection[0]})

    def open_mod(self):
        selection = self.mod_list.selection()
        try:
            if not self.ready():
                return
            if selection:
                self.open_folder(confined(self.toolkit.workspace, selection[0]))
            else:
                self.status.set("Select a development mod first.")
        except (OSError, ValueError) as exc:
            self.display("Could not open the mod folder.", str(exc), "error")

    def open_reports(self):
        try:
            if self.ready():
                self.open_folder(confined(self.toolkit.profile, "reports"))
        except (OSError, ValueError) as exc:
            self.display("Could not open reports.", str(exc), "error")

    def open_folder(self, path):
        try:
            if not path.is_dir():
                raise ValueError("Folder does not exist yet. Complete the related action first.")
            if os.name != "nt":
                raise ValueError(f"Open this folder in your file manager: {path}")
            os.startfile(str(path))
        except (OSError, ValueError) as exc:
            self.display("Could not open the folder.", str(exc), "error")

    def refresh_scenarios(self):
        if not self.ready() or not self.discard_changes():
            return
        try:
            folder = confined(self.toolkit.workspace, "scenarios")
            values = [path.relative_to(self.toolkit.workspace).as_posix() for path in sorted(folder.glob("*.lua"))
                      if not linked(path) and path.is_file()]
            self.scenarios.configure(values=values)
            self.scenario.set(self.loaded_scenario if self.loaded_scenario in values else (values[0] if values else ""))
            self.load_scenario()
        except (OSError, ValueError) as exc:
            self.display("Could not read scenarios.", str(exc), "error")

    def editor_changed(self, event=None):
        if self.editor.edit_modified():
            self.scenario_note.set("Unsaved changes. Save the scenario before running it.")

    def discard_changes(self):
        if not self.loaded_scenario or not self.editor.edit_modified():
            return True
        answer = messagebox.askyesnocancel("Unsaved scenario", "Save scenario changes before continuing?", parent=self.root)
        if answer is None:
            return False
        if answer:
            return self.save_scenario()
        self.editor.edit_modified(False)
        return True

    def load_scenario(self, event=None):
        if not self.toolkit:
            return
        if not self.discard_changes():
            self.scenario.set(self.loaded_scenario or "")
            return
        try:
            name = self.scenario.get()
            code = ""
            if name:
                path = confined(self.toolkit.workspace, name)
                if path.suffix != ".lua" or path.stat().st_size > 60 * 1024:
                    raise ValueError("Choose a Lua scenario no larger than 60 KiB")
                code = path.read_text(encoding="utf-8-sig")
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", code)
            self.editor.edit_modified(False)
            self.loaded_scenario = name or None
            self.trusted.set(False)
            self.scenario_note.set("Saved scenario. Edit here or run it in the loaded game." if name else "Create a mod to generate a smoke scenario.")
        except (OSError, ValueError) as exc:
            self.scenario.set(self.loaded_scenario or "")
            self.display("Could not load the scenario.", str(exc), "error")

    def save_scenario(self):
        if not self.toolkit or not self.loaded_scenario:
            self.status.set("Choose a scenario first.")
            return False
        try:
            code = self.editor.get("1.0", "end-1c")
            if len(code.encode("utf-8")) > 60 * 1024:
                raise ValueError("Scenario exceeds 60 KiB")
            atomic_text(confined(self.toolkit.workspace, self.loaded_scenario), code)
            self.editor.edit_modified(False)
            self.scenario_note.set("Scenario saved.")
            return True
        except (OSError, ValueError) as exc:
            self.display("Scenario was not saved.", str(exc), "error")
            return False

    def run_scenario(self):
        if not self.loaded_scenario:
            self.status.set("Choose a saved scenario first.")
            return
        if self.editor.edit_modified():
            self.status.set("Save your scenario changes before running.")
            return
        if not self.trusted.get():
            self.status.set("Review the Lua scenario and select the trust checkbox before running.")
            return
        try:
            timeout = float(self.timeout.get())
        except ValueError:
            self.status.set("Enter a timeout between 0.1 and 300 seconds.")
            return
        self.dispatch("harness_run", {"scenario": self.loaded_scenario, "timeout": timeout})

    def settings_changed(self, *_):
        if self.toolkit and any(value.get() != self.saved_paths.get(key) for key, value in self.paths.items()):
            self.status.set("Setup changed. Save setup before using the toolkit.")

    def ready(self):
        if not self.toolkit:
            self.tabs.select(self.setup)
            self.status.set("Save a valid setup before using the toolkit.")
            return False
        if any(value.get() != self.saved_paths.get(key) for key, value in self.paths.items()):
            self.tabs.select(self.setup)
            self.status.set("Setup changed. Save setup before using the toolkit.")
            return False
        return True

    def dispatch(self, name, arguments=None, callback=None):
        if self.busy or not self.ready():
            return
        toolkit, arguments = self.toolkit, arguments or {}
        self.start_job(name, lambda: toolkit.call(name, arguments), callback)

    def start_job(self, name, operation, callback=None):
        if self.busy:
            return
        self.busy = True
        self.last_result = None
        for button in self.actions:
            button.configure(state="disabled")
        for entry in self.path_entries:
            entry.configure(state="disabled")
        self.scenarios.configure(state="disabled")
        self.editor.configure(state="disabled")
        self.clear_guide_arrow()
        for button in (self.guide_next, self.guide_previous, self.guide_show):
            button.configure(state="disabled")
        self.progress.pack(side="right")
        self.progress.start(15)
        self.status.set("Running scenario in the game. Waiting for a matching response…" if name == "harness_run" else
                        f"Working: {name.replace('_', ' ')}…")

        def worker():
            try:
                self.jobs.put((name, operation(), None, callback))
            except Exception as exc:
                self.jobs.put((name, None, str(exc) or type(exc).__name__, None))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            self.deliver_job()
        finally:
            self.poll_handle = self.root.after(80, self.poll)

    def deliver_job(self):
        try:
            name, result, error, callback = self.jobs.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.progress.stop()
            self.progress.pack_forget()
            for button in self.actions:
                button.configure(state="normal")
            for entry in self.path_entries:
                entry.configure(state="normal")
            self.scenarios.configure(state="readonly")
            self.editor.configure(state="normal")
            self.guide_show.configure(state="normal")
            self.guide_previous.configure(state="disabled" if self.guide_index == 0 else "normal")
            self.guide_next.configure(state="disabled" if self.guide_index == len(GUIDE) - 1 else "normal")
            self.last_result = {"error": error} if error else result
            summary = f"Completed: {name.replace('_', ' ')}."
            if error:
                summary = "Action could not complete. See the details below."
            elif result.get("status") == "timed_out":
                summary = "No matching game response. The test outcome is unknown."
            elif result.get("status") == "invalid_response":
                summary = "The bridge response was malformed. The test outcome is unknown."
            elif result.get("ok") is False:
                summary = "Test failed." if name == "harness_run" else "Check found a problem. See the details below."
            elif name == "harness_run":
                summary = f"Test passed. {result.get('message', '')}"
            elif name == "bridge_status":
                summary = "Bridge ready. You can run a scenario." if result.get("ready") else result.get("next_step", "Bridge is not ready.")
            tone = "error" if error or result.get("ok") is False else "info"
            if result and (result.get("status") in ("timed_out", "invalid_response")
                           or name == "bridge_status" and not result.get("ready")):
                tone = "warning"
            self.display(summary, error or result, tone)
            if callback and not error and result.get("ok") is not False:
                try:
                    callback(result)
                except (OSError, ValueError, tk.TclError) as exc:
                    self.display("Action completed, but the workspace view could not refresh.", str(exc), "warning")
            if not error and result.get("ok") is not False and (name != "bridge_status" or result.get("ready")):
                self.advance_guide(name)
            self.point_guide()

    def close(self):
        if self.busy:
            self.status.set("Wait for the current action to finish before closing. Closing cannot cancel Lua already running.")
        elif self.discard_changes():
            self.root.after_cancel(self.poll_handle)
            self.clear_guide_arrow()
            for value, trace in self.path_traces:
                value.trace_remove("write", trace)
            self.status.trace_remove("write", self.status_trace)
            self.root.destroy()
            # Release Tk images on the UI thread, including repeated test windows.
            del self.header_logo, self.icon


def main():
    parser = argparse.ArgumentParser(description="Project Zomboid Toolkit desktop app")
    parser.add_argument("--config", type=Path, default=default_config())
    parser.add_argument("--smoke-report", type=Path, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    root = tk.Tk()
    app = Application(root, arguments.config)
    if arguments.smoke_report:
        # Build verification exercises the real window and bundled assets, not a game.
        import time

        root.geometry("1100x860")
        started = time.monotonic()

        def verify():
            if app.busy and time.monotonic() - started < 30:
                root.after(100, verify)
                return
            bridge = app.toolkit.profile / "mods/PZToolkitBridge" if app.toolkit else None
            assets = bool(bridge and (bridge / "42/media/lua/client/PZToolkitBridge.lua").is_file()
                          and (bridge / "common/README.txt").is_file())
            setup_buttons = [button for button in app.actions if str(button).startswith(str(app.setup) + ".")]
            controls_fit = all(button.winfo_ismapped()
                               and app.setup.winfo_rootx() <= button.winfo_rootx()
                               and button.winfo_rootx() + button.winfo_width() <= app.setup.winfo_rootx() + app.setup.winfo_width()
                               and button.winfo_rooty() + button.winfo_height() <= app.setup.winfo_rooty() + app.setup.winfo_height()
                               for button in setup_buttons)
            app.tabs.select(app.tests)
            root.update_idletasks()
            test_controls = [button for button in app.actions if str(button).startswith(str(app.tests) + ".")]
            test_controls += [widget for widget in app.tests.winfo_children() if isinstance(widget, ttk.Checkbutton)]
            test_controls_fit = all(button.winfo_ismapped()
                                    and app.tests.winfo_rootx() <= button.winfo_rootx()
                                    and button.winfo_rootx() + button.winfo_width() <= app.tests.winfo_rootx() + app.tests.winfo_width()
                                    and button.winfo_rooty() + button.winfo_height() <= app.tests.winfo_rooty() + app.tests.winfo_height()
                                    for button in test_controls)
            result = {"ok": bool(not app.busy and app.last_result and app.last_result.get("ok") and assets),
                      "window_mapped": bool(root.winfo_ismapped()), "bridge_assets": assets,
                      "branding_loaded": app.header_logo.width() > 0,
                      "display_font": app.display_family,
                      "navigation": list(app.navigation), "guide_steps": len(GUIDE),
                      "setup_controls_fit": controls_fit,
                      "test_controls_fit": test_controls_fit,
                      "tabs": [app.tabs.tab(page, "text") for page in app.tabs.tabs()]}
            atomic_text(arguments.smoke_report, json.dumps(result))
            root.after_cancel(app.poll_handle)
            root.destroy()

        def start():
            app.dispatch("profile_prepare")
            root.after(100, verify)
        root.after(150, start)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
