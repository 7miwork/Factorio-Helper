"""Tab: Scan-Ergebnisse der Mods (Tabelle + Abhängigkeiten)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..factorio.mod_scanner import parse_dependency


class ModsTab(ttk.Frame):
    COLUMNS = ("name", "title", "version", "enabled", "source")

    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self._entries = []
        self._build()

    def _build(self) -> None:
        self.summary = tk.StringVar(value="Noch kein Scan durchgeführt.")
        ttk.Label(self, text="Installierte Mods").pack(anchor="w")
        ttk.Label(self, textvariable=self.summary).pack(anchor="w", pady=(2, 6))

        self.tree = ttk.Treeview(self, columns=self.COLUMNS, show="headings", height=12)
        headings = (("name", "Mod"), ("title", "Titel"), ("version", "Version"),
                    ("enabled", "Status"), ("source", "Quelle"))
        for key, text in headings:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=130)
        self.tree.column("source", width=230)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        ttk.Label(self, text="Abhängigkeiten (ausgewählte Mod)").pack(anchor="w", pady=(8, 2))
        self.deps = tk.Text(self, height=8, state="disabled")
        self.deps.pack(fill="x")

    # ------------------------------------------------------------------ #
    def populate(self, mods: list) -> None:
        self._entries = list(mods)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for mod in mods:
            state = "aktiv" if mod.enabled else "inaktiv"
            self.tree.insert("", "end", iid=str(mod.source),
                             values=(mod.name, mod.title, mod.version, state, mod.source))
        self.summary.set(f"{len(mods)} Mod(s) erkannt. Auswahl zeigt die Abhängigkeiten.")

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        self.deps.configure(state="normal")
        self.deps.delete("1.0", tk.END)
        if selection:
            iid = selection[0]
            mod = next((m for m in self._entries if str(m.source) == iid), None)
            if mod:
                self.deps.insert(tk.END, self._format_dependencies(mod))
        self.deps.configure(state="disabled")

    def _format_dependencies(self, mod) -> str:
        lines = [f"{mod.name} ({mod.version}):"]
        if not mod.dependencies:
            lines.append("  – keine")
            return "\n".join(lines)
        for name in mod.dependencies:
            parsed = parse_dependency(name)
            lines.append(
                f"  • {parsed['name']}"
                + (f"  {parsed['operator']} {parsed['version']}" if parsed["version"] else "")
                + ("  (optional)" if parsed["optional"] else "")
                + ("  (versteckt)" if parsed["hidden"] else "")
            )
        return "\n".join(lines)