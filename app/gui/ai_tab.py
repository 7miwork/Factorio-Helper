"""Tab: KI-Provider und Modelle konfigurieren (Ollama, LM Studio, ...).

Die Modell-Erkennung laeuft in einem Hintergrund-Thread, damit die GUI nicht
einfriert. Bei Ollama/OpenAI-kompatiblen Endpoints markiert das Tab konfigurierte
Modelle, die nicht (bzw. nicht installiert) gefunden wurden.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk

from ..ai.manager import ProviderManager
from ..knowledge.context import load_learning_notes, save_learning_notes


class AISettingsTab(ttk.Frame):
    NOT_INSTALLED_SUFFIX = "  (nicht installiert)"

    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.config_path = main.project_root / "config" / "ai_providers.json"
        self.manager = ProviderManager(self.config_path)
        self._queue = queue.Queue()

        self.provider_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.base_var = tk.StringVar()
        self.status = tk.StringVar(value="Provider wählen und Modelle aktualisieren.")
        self._build()
        self.after(50, self._poll_results)
        self._refresh_providers()
        self._build_notes()

    def _build(self) -> None:
        ttk.Label(self, text="KI Provider").pack(anchor="w")
        ttk.Label(self, text="Provider").pack(anchor="w", pady=(8, 2))
        self.provider_box = ttk.Combobox(self, textvariable=self.provider_var, state="readonly")
        self.provider_box.pack(fill="x")
        self.provider_box.bind("<<ComboboxSelected>>", self._on_provider)

        ttk.Label(self, text="Modell").pack(anchor="w", pady=(8, 2))
        self.model_box = ttk.Combobox(self, textvariable=self.model_var, state="readonly")
        self.model_box.pack(fill="x")

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=10)
        ttk.Button(actions, text="Modelle aktualisieren", command=self.refresh_models).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Modelle auflisten", command=self.list_models).pack(side="left")

        ttk.Label(self, text="Base URL").pack(anchor="w", pady=(8, 2))
        ttk.Entry(self, textvariable=self.base_var, state="readonly").pack(fill="x")
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=10)

    # ------------------------------------------------------------------ #
    def _refresh_providers(self) -> None:
        providers = list(self.manager.config.get("providers", {}).keys())
        self.provider_box["values"] = providers
        active = self.manager.config.get("active_provider", "mock")
        self.provider_var.set(active if active in providers else (providers[0] if providers else ""))
        self._on_provider()

    def _on_provider(self, _event=None) -> None:
        name = self.provider_var.get()
        if not name:
            return
        setting = self.manager.config.get("providers", {}).get(name, {})
        self.base_var.set(str(setting.get("base_url", "")))
        self._set_models(name)

    def _set_models(self, name: str) -> None:
        """Zeigt die (lokalen) konfigurierten Modelle ohne Netzwerkaufruf."""
        try:
            configured = self.manager.models(name, refresh=False)
        except ValueError:
            configured = []
        self._apply_models(name, discovered=None, configured=configured)

    # ------------------------------------------------------------------ #
    def refresh_models(self) -> None:
        name = self.provider_var.get()
        if not name:
            return
        self.status.set(f"Modelle für {name} werden geladen …")
        threading.Thread(target=self._refresh_worker, args=(name,), daemon=True).start()

    def _refresh_worker(self, name: str) -> None:
        try:
            discovered = self.manager.models(name, refresh=True)
            configured = self.manager.models(name, refresh=False)
        except Exception as error:  # noqa: BLE001 – Netzwerkfehler sind erwartbar
            self._queue.put(("error", str(error)))
        else:
            self._queue.put(("ok", name, discovered, configured))

    def _poll_results(self) -> None:
        try:
            while True:
                item = self._queue.get_nowait()
                if item[0] == "ok":
                    self._apply_models(*item[1:])
                elif item[0] == "error":
                    self.status.set(f"Modell-Erkennung fehlgeschlagen: {item[1]}")
        except queue.Empty:
            pass
        self.after(50, self._poll_results)

    def _apply_models(self, provider: str, discovered, configured: list) -> None:
        """Baut die Modellliste; konfigurierte, nicht gefundene Modelle werden markiert."""
        discovered = list(discovered or [])
        discovered_set = set(discovered)
        values = []
        for cfg in configured:
            if discovered_set and cfg not in discovered_set:
                values.append(f"{cfg}{self.NOT_INSTALLED_SUFFIX}")
            else:
                values.append(cfg)
        # Zusätzlich gefundene, aber nicht vorkonfigurierte Modelle anfügen.
        seen = set(values)
        for discovered_name in discovered:
            if discovered_name not in seen:
                values.append(discovered_name)
                seen.add(discovered_name)

        self.model_box["values"] = values

        if discovered_set:
            preferred = next((cfg for cfg in configured if cfg in discovered_set), None)
        else:
            preferred = configured[0] if configured else None
        self.model_var.set(preferred if preferred else (values[0] if values else ""))

        if discovered_set:
            self.status.set(f"{provider}: {len(discovered)} installierte(s)/erreichbare(s) Modell(e), "
                            f"{len(configured)} konfiguriert.")
        else:
            self.status.set(f"{provider}: Modellliste aus Konfiguration ({len(configured)}).")

    def list_models(self) -> None:
        name = self.provider_var.get()
        if not name:
            return
        try:
            self._set_models(name)
            self.status.set(f"Konfigurierte Modelle für {name}: {len(self.model_box['values'])}")
        except ValueError as error:  # z. B. deaktivierter Provider
            self.status.set(str(error))
# ------------------------------------------------------------------ #
    # Lern-Notizen (eigene Eingaben, aus denen die KI lernen soll)
    # ------------------------------------------------------------------ #
    def _build_notes(self) -> None:
        notes_box = ttk.LabelFrame(self, text="Lern-Notizen (werden dem KI-Planner mitgegeben)", padding=8)
        notes_box.pack(fill="x", pady=(12, 0))
        self.notes_text = tk.Text(notes_box, height=6, wrap="word")
        self.notes_text.pack(fill="x")
        self.notes_text.insert("1.0", load_learning_notes())
        footer = ttk.Frame(notes_box)
        footer.pack(fill="x", pady=(6, 0))
        ttk.Button(footer, text="Notizen speichern", command=self.save_notes).pack(side="left")
        self.notes_status = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.notes_status).pack(side="left", padx=(10, 0))

    def save_notes(self) -> None:
        save_learning_notes(self.notes_text.get("1.0", "end").strip())
        self.notes_status.set("Gespeichert (data/learn/notes.md) – wird beim nächsten Planen einbezogen.")