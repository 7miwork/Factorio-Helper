"""Tab: Einstellungen und Projektpfade."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..utils import paths


class SettingsTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Einstellungen").pack(anchor="w")
        ttk.Label(self, text="Factorio-Installationspfad").pack(anchor="w", pady=(10, 2))
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.path_entry = ttk.Entry(row, textvariable=self.main.factorio_path)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Pfad übernehmen", command=self.apply_path).pack(side="left", padx=(8, 0))
        ttk.Button(row, text="Speichern", command=self.save).pack(side="left", padx=(8, 0))

        ttk.Label(self, text="Projektpfade").pack(anchor="w", pady=(18, 4))
        self._path_table = []
        for label, path in (
            ("settings.json", paths.SETTINGS_PATH),
            ("ai_providers.json", paths.AI_PROVIDERS_FILE),
            ("blueprints/", paths.BLUEPRINTS_DIR),
            ("logs/", paths.LOGS_DIR),
            ("data/", paths.DATA_DIR),
        ):
            frame = ttk.Frame(self)
            frame.pack(fill="x", anchor="w")
            ttk.Label(frame, text=f"{label}:", width=18).pack(side="left", anchor="w")
            ttk.Label(frame, text=str(path)).pack(side="left", anchor="w")
            self._path_table.append(path)

        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=12)

    # ------------------------------------------------------------------ #
    def apply_path(self) -> None:
        self.main.factorio_path.set(self.path_entry.get())
        self.status.set("Pfad in das Feld der Installation übernommen.")

    def save(self) -> None:
        self.main.factorio_path.set(self.path_entry.get())
        self.main.save_settings()
        self.status.set("Einstellungen in config/settings.json gespeichert.")
        messagebox.showinfo("Einstellungen", "Einstellungen wurden gespeichert.")