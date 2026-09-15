"""Tab: Knowledge Base aus der installierten Factorio-Installation aufbauen."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..knowledge.builder import build_knowledge_base


class KnowledgeTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.status = tk.StringVar(value="Noch keine Knowledge Base erstellt.")
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Knowledge Base").pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Sammelt Items, Entities, Rezepte, Technologien, Fluids, Ressourcen "
                "und Module aus den installierten Daten (JSON-Prototypen) in einer "
                "lokalen SQLite-Datenbank."
            ),
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(6, 10))
        ttk.Button(self, text="Knowledge Base aufbauen", command=self.build).pack(anchor="w")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=10)
        self.output = tk.Text(self, height=16, width=90, state="disabled")
        self.output.pack(fill="both", expand=True)

    def build(self) -> None:
        path = self.main.factorio_path.get().strip() or str(self.main.settings.get("factorio_path", ""))
        if not path:
            messagebox.showwarning("Kein Pfad", "Bitte zuerst eine Installation analysieren.")
            return
        try:
            count = build_knowledge_base(path, self.main.project_root)
        except Exception as error:  # noqa: BLE001 – Benutzerinfo
            messagebox.showerror("Knowledge Base fehlgeschlagen", str(error))
            return
        self.status.set(f"Knowledge Base: {count} Prototyp(en) importiert (data/factorio/knowledge.db).")
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"Importierte Prototypen: {count}\nDatenbank: data/factorio/knowledge.db\n")
        self.output.configure(state="disabled")