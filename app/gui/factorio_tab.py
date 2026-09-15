"""Tab: Factorio-Installation auswählen und analysieren (Version, Mods)."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..factorio.detector import detect_installation
from ..factorio.mod_scanner import mod_to_dict, scan_mods


class FactorioTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.path_var = main.factorio_path
        self.status = tk.StringVar(
            value="Bitte eine Factorio-Installation wählen oder angeben und analysieren."
        )
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Factorio Installation").pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(6, 12))
        ttk.Entry(row, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Ordner wählen", command=self.choose_folder).pack(side="left", padx=(8, 0))
        ttk.Button(self, text="Installation analysieren", command=self.analyze).pack(anchor="w")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=10)
        self.output = tk.Text(self, height=22, width=90, state="disabled")
        self.output.pack(fill="both", expand=True)

    def choose_folder(self) -> None:
        initial = self.path_var.get() or None
        folder = filedialog.askdirectory(title="Factorio-Ordner auswählen", initialdir=initial)
        if folder:
            self.path_var.set(folder)

    def analyze(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("Kein Pfad", "Bitte zuerst einen Factorio-Ordner wählen.")
            return
        try:
            installation = detect_installation(path)
            mods = scan_mods(installation.path)
        except Exception as error:  # noqa: BLE001 – Benutzerinfo
            messagebox.showerror("Scan fehlgeschlagen", str(error))
            return

        result = {
            "path": str(installation.path),
            "version": installation.version or "unknown",
            "mods": [mod_to_dict(mod) for mod in mods],
        }
        self.status.set(f"Version: {result['version']} | Mods: {len(result['mods'])}")
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, json.dumps(result, indent=2))
        self.output.configure(state="disabled")

        self.main.settings["factorio_path"] = str(installation.path)
        self.main.save_settings()
        self.main.on_scan(result, mods)