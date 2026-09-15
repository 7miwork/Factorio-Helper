"""Hauptfenster: Notebook mit den einzelnen Fach-Tabs."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..utils import paths
from .ai_tab import AISettingsTab
from .factorio_tab import FactorioTab
from .generator_tab import GeneratorTab
from .knowledge_tab import KnowledgeTab
from .library_tab import LibraryTab
from .mods_tab import ModsTab
from .settings_tab import SettingsTab


class MainWindow:
    """Baut das Hauptfenster mit allen Tabs und teilt den gemeinsamen Zustand."""

    TABS = (
        ("Installation", FactorioTab),
        ("Mods", ModsTab),
        ("Generator", GeneratorTab),
        ("Knowledge Base", KnowledgeTab),
        ("AI Settings", AISettingsTab),
        ("Library", LibraryTab),
        ("Settings", SettingsTab),
    )

    def __init__(self, root: tk.Tk):
        self.root = root
        self.settings = paths.load_settings()
        self.project_root = paths.ROOT
        self.factorio_path = tk.StringVar(value=str(self.settings.get("factorio_path", "")))
        self.last_install = None
        self.last_mods = []  # list[ModInfo]

        self.root.title("Factorio AI Blueprint Generator")
        self.root.geometry("920x640")
        self._build()

    def _build(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.tabs = {}
        for label, cls in self.TABS:
            tab = cls(self.notebook, self)
            self.tabs[label] = tab
            self.notebook.add(tab, text=label)

    # ------------------------------------------------------------------ #
    def on_scan(self, install_info: dict, mods: list) -> None:
        """Wird vom Factorio-Tab nach einem erfolgreichen Scan aufgerufen."""
        self.last_install = install_info
        self.last_mods = list(mods)
        self.tabs["Mods"].populate(mods)

    def save_settings(self) -> None:
        self.settings["factorio_path"] = self.factorio_path.get()
        paths.save_settings(self.settings)