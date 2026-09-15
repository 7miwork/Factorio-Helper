"""Tab: Blueprint Library (gespeicherte Blueprints auflisten und Book erzeugen)."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from ..library.book import create_book, save_book
from ..library.manager import LibraryManager


class LibraryTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.manager = LibraryManager(main.project_root / "blueprints")
        self.status = tk.StringVar(value="Noch keine Blueprints gespeichert.")
        self._build()
        self.refresh()

    def _build(self) -> None:
        ttk.Label(self, text="Blueprint Library").pack(anchor="w")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=(2, 8))
        columns = ("slug", "name", "entities")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        for key, text in (("slug", "Ordner"), ("name", "Name"), ("entities", "Entities")):
            self.tree.heading(key, text=text)
            self.tree.column(key, width=200)
        self.tree.pack(fill="both", expand=True)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Aktualisieren", command=self.refresh).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Blueprint Book erzeugen", command=self.export_book).pack(side="left")

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        entries = self.manager.list()
        for entry in entries:
            self.tree.insert("", "end", values=(entry.get("slug", ""), entry.get("name", ""), entry.get("entities", 0)))
        self.status.set(f"{len(entries)} Blueprint(s) in blueprints/.")

    def export_book(self) -> None:
        book_paths = sorted(self.manager.root.glob("*/blueprint.json"))
        if not book_paths:
            messagebox.showinfo("Blueprint Book", "Es sind noch keine Blueprints gespeichert.")
            return
        blueprints = []
        for path in book_paths:
            try:
                blueprints.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        if not blueprints:
            messagebox.showinfo("Blueprint Book", "Keine gültigen Blueprints gefunden.")
            return
        book = create_book("Factorio AI Blueprint Book", blueprints)
        destination = save_book(self.manager.root / "book", book)
        self.status.set(f"Blueprint Book gespeichert: {destination} (+ .txt)")
        messagebox.showinfo("Blueprint Book", f"Blueprint Book mit {len(blueprints)} Blueprints gespeichert.")