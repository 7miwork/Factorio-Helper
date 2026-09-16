"""Tab: Knowledge Base aufbauen und Prototypen mit Grafikvorschau anzeigen.

Nach dem Aufbau (oder Laden der vorhandenen Datenbank) werden die Prototypen in
einer Liste angezeigt. Die Auswahl zeigt die Metadaten und – falls verfügbar –
die Spielgrafik (Icon) als Vorschau.
"""
from __future__ import annotations

import base64
import tkinter as tk
from tkinter import messagebox, ttk

from ..factorio.mod_scanner import scan_mods
from ..graphics.loader import graphic_path
from ..graphics.preview import preview_bytes, description
from ..knowledge.builder import build_knowledge_base
from ..knowledge.database import KnowledgeBase, database_path

COLUMNS = ("name", "type", "mod")


class KnowledgeTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.status = tk.StringVar(value="Noch keine Knowledge Base erstellt.")
        self._prototypes = []
        self._mods = []
        self._preview_photo = None  # Referenz gegen Garbage-Collection halten
        self._current_proto = None
        self._build()
        self._try_load_existing()

    # ------------------------------------------------------------------ #
    def _build(self) -> None:
        ttk.Label(self, text="Knowledge Base").pack(anchor="w")
        hint = (
            "Sammelt Items, Entities, Rezepte, Technologien, Fluids, Ressourcen und Module "
            "aus den installierten Daten in einer lokalen SQLite-Datenbank. Die Auswahl "
            "eines Eintrags zeigt Metadaten und – falls vorhanden – die Spielgrafik."
        )
        ttk.Label(self, text=hint, wraplength=720, justify="left").pack(anchor="w", pady=(4, 8))
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, 8))
        ttk.Button(row, text="Knowledge Base aufbauen", command=self.build).pack(side="left")
        ttk.Label(row, textvariable=self.status).pack(side="left", padx=(12, 0))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        list_frame = ttk.Frame(body)
        list_frame.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=COLUMNS, show="headings", height=18)
        for key, text, width in (("name", "Name", 200), ("type", "Typ", 110), ("mod", "Mod", 160)):
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        detail = ttk.Frame(body, width=360, padding=(10, 0, 0, 0))
        detail.pack(side="right", fill="y")
        detail.pack_propagate(False)
        ttk.Label(detail, text="Vorschau").pack(anchor="w")
        scale_row = ttk.Frame(detail)
        scale_row.pack(fill="x", pady=(2, 5))
        self.scale_var = tk.StringVar(value="1x")
        self.scale_box = ttk.Combobox(scale_row, textvariable=self.scale_var, state="readonly",
                                      values=("1x", "2x", "3x", "4x"), width=6)
        self.scale_box.pack(side="left")
        self.preview_info = tk.StringVar(value="")
        ttk.Label(scale_row, textvariable=self.preview_info, anchor="w").pack(side="left", fill="x", expand=True)
        self.scale_box.bind("<<ComboboxSelected>>", self._on_scale)
        self.preview_label = ttk.Label(detail, text="(keine Auswahl)", anchor="center")
        self.preview_label.pack(fill="x", pady=(4, 8))
        ttk.Label(detail, text="Metadaten").pack(anchor="w")
        self.meta = tk.Text(detail, height=14, width=42, state="disabled")
        self.meta.pack(fill="both", expand=True)
# ------------------------------------------------------------------ #
    def _try_load_existing(self) -> None:
        db_path = database_path(self.main.project_root)
        if db_path.is_file():
            try:
                self._load_from_db()
            except Exception:  # noqa: BLE001 – DB könnte defekt sein
                pass

    def _load_from_db(self) -> None:
        database = KnowledgeBase(database_path(self.main.project_root))
        try:
            self._prototypes = database.find()
        finally:
            database.close()
        self.status.set(f"Knowledge Base geladen: {len(self._prototypes)} Prototyp(en).")
        self._refresh_tree()

    def build(self) -> None:
        path = self.main.factorio_path.get().strip() or str(self.main.settings.get("factorio_path", ""))
        if not path:
            messagebox.showwarning("Kein Pfad", "Bitte zuerst eine Installation analysieren.")
            return
        try:
            count = build_knowledge_base(path, self.main.project_root)
            self._mods = scan_mods(path)
        except Exception as error:  # noqa: BLE001 – Benutzerinfo
            messagebox.showerror("Knowledge Base fehlgeschlagen", str(error))
            return
        self.install_path = path
        self._load_from_db()
        self.status.set(f"Knowledge Base: {count} Prototyp(en) importiert (data/factorio/knowledge.db).")

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, proto in enumerate(self._prototypes):
            self.tree.insert("", "end", iid=str(index),
                             values=(proto.name, proto.prototype_type, proto.source_mod))

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        self.meta.configure(state="normal")
        self.meta.delete("1.0", tk.END)
        self._current_proto = None
        self._reset_preview()
        if not selection:
            self.meta.configure(state="disabled")
            return
        proto = self._prototypes[int(selection[0])]
        self._show_metadata(proto)
        self._show_preview(proto)
        self.meta.configure(state="disabled")

    def _show_metadata(self, proto) -> None:
        lines = [
            f"Name: {proto.name}",
            f"Typ: {proto.prototype_type}",
            f"Mod: {proto.source_mod}",
            f"Quelle: {proto.source_file}",
            "",
            "Daten:",
        ]
        data = proto.data if isinstance(proto.data, dict) else {}
        for key in ("version", "stack_size", "crafting_categories", "category", "result"):
            if key in data:
                lines.append(f"  {key}: {data[key]}")
        self.meta.insert(tk.END, "\n".join(lines))

    def _reset_preview(self) -> None:
        self.preview_label.config(image="", text="(keine Auswahl)")
        self.preview_info.set("")
        self._preview_photo = None

    def _scale_value(self) -> float:
        text = (self.scale_var.get() or "1x").strip()
        if text.endswith("%"):
            return max(0.1, round(float(text[:-1]) / 100.0, 2))
        if text.endswith("x"):
            return float(text[:-1])
        return float(text)

    def _on_scale(self, _event=None) -> None:
        if self._current_proto is not None:
            self._show_preview(self._current_proto)

    def _show_preview(self, proto) -> None:
        self._current_proto = proto
        install_path = (
            getattr(self, "install_path", None)
            or self.main.factorio_path.get().strip()
            or str(self.main.settings.get("factorio_path", ""))
        )
        if not install_path:
            return
        try:
            graphic = graphic_path(install_path, self._mods, proto.data or {})
        except Exception:  # noqa: BLE001
            graphic = None
        if graphic is None:
            self.preview_label.config(image="", text="(Vorschau nicht verfügbar)")
            self.preview_info.set("")
            return
        try:
            scale = self._scale_value()
            png_bytes, width, height = preview_bytes(graphic, scale)
            self._preview_photo = tk.PhotoImage(data=base64.b64encode(png_bytes).decode("ascii"))
            self.preview_label.config(image=self._preview_photo, text="")
            self.preview_info.set(f"{width}×{height}  {description(scale)}")
        except Exception as error:  # noqa: BLE001 – z. B. DXT-/DDS ohne Decoder
            self.preview_label.config(image="", text="(Grafik konnte nicht geladen werden)")
            self.preview_info.set(str(error))