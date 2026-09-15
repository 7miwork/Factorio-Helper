"""Tab: Blueprint-Generator (Plan aus Anforderungen erzeugen)."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from ..workflow import generate_from_requirements


class GeneratorTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.requirements = tk.StringVar(value="Erstelle eine erweiterbare Starter Base.")
        self.slug = tk.StringVar(value="generated")
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Anforderungen").pack(anchor="w")
        ttk.Entry(self, textvariable=self.requirements).pack(fill="x", pady=(6, 10))
        ttk.Label(self, text="Library-Name").pack(anchor="w")
        ttk.Entry(self, textvariable=self.slug).pack(fill="x", pady=(6, 10))
        ttk.Button(self, text="Blueprint erzeugen", command=self.generate).pack(anchor="w")
        self.output = tk.Text(self, height=22, width=90, state="disabled")
        self.output.pack(fill="both", expand=True, pady=(10, 0))

    def generate(self) -> None:
        try:
            result = generate_from_requirements(
                self.requirements.get(), self.main.project_root, self.slug.get()
            )
        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("Erzeugung fehlgeschlagen", str(error))
            return
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, json.dumps(result, indent=2))
        self.output.configure(state="disabled")
        # Bibliothek im Library-Tab aktualisieren, falls vorhanden.
        library = self.main.tabs.get("Library")
        if library is not None:
            library.refresh()