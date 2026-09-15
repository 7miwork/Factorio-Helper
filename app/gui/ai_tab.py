"""Tab: KI-Provider und Modelle konfigurieren (Ollama, LM Studio, ...)."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..ai.manager import ProviderManager


class AISettingsTab(ttk.Frame):
    def __init__(self, parent, main):
        super().__init__(parent, padding=16)
        self.main = main
        self.config_path = main.project_root / "config" / "ai_providers.json"
        self.manager = ProviderManager(self.config_path)

        self.provider_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.base_var = tk.StringVar()
        self.status = tk.StringVar(value="Provider wählen und Modelle aktualisieren.")
        self._build()
        self._refresh_providers()

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
        try:
            models = self.manager.models(name, refresh=False)
        except ValueError:
            models = []
        self.model_box["values"] = models
        self.model_var.set(models[0] if models else "")

    def refresh_models(self) -> None:
        name = self.provider_var.get()
        if not name:
            return
        try:
            models = self.manager.models(name, refresh=True)
        except Exception as error:  # noqa: BLE001 – Netzwerkfehler
            self.status.set(f"Modell-Erkennung fehlgeschlagen: {error}")
            messagebox.showinfo("Modell-Erkennung", str(error))
            return
        self.model_box["values"] = models
        self.model_var.set(models[0] if models else "")
        self.status.set(f"{len(models)} Modell(e) für {name}.")

    def list_models(self) -> None:
        name = self.provider_var.get()
        if not name:
            return
        try:
            self._set_models(name)
            self.status.set(f"Konfigurierte Modelle für {name}: {len(self.model_box['values'])}")
        except ValueError as error:  # z. B. deaktivierter Provider
            self.status.set(str(error))