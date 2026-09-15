import json
from pathlib import Path

from app.ai.lmstudio import LMStudioProvider
from app.ai.mock import MockProvider
from app.ai.ollama import list_models as list_ollama_models
from app.ai.openai_compatible import OpenAICompatibleProvider


class ProviderManager:
    def __init__(self, config_path: str | Path):
        self.config = json.loads(Path(config_path).read_text(encoding="utf-8"))

    def _settings(self, name: str) -> dict:
        settings = self.config["providers"][name]
        if not settings.get("enabled", False):
            raise ValueError(f"Provider disabled: {name}")
        return settings

    def provider(self, name: str | None = None):
        name = name or self.config.get("active_provider", "mock")
        settings = self._settings(name)
        if settings["type"] == "mock":
            return MockProvider()
        if settings["type"] == "ollama":
            return OpenAICompatibleProvider(settings["base_url"].rstrip("/") + "/v1")
        if name == "lmstudio":
            return LMStudioProvider(settings["base_url"], settings.get("api_key_env", ""))
        return OpenAICompatibleProvider(settings["base_url"], settings.get("api_key_env", ""))

    def complete(self, prompt: str, role: str = "planner") -> str:
        role_config = self.config.get("roles", {}).get(role, {})
        provider_name = role_config.get("provider") or self.config.get("active_provider", "mock")
        model = role_config.get("model", "builtin")
        return self.provider(provider_name).complete(prompt, model)

    def ollama_models(self) -> list[str]:
        settings = self._settings("ollama")
        return list_ollama_models(settings["base_url"])

    def models(self, name: str | None = None, refresh: bool = False) -> list[str]:
        provider_name = name or self.config.get("active_provider", "mock")
        settings = self._settings(provider_name)
        if refresh and settings["type"] == "ollama":
            return self.ollama_models()
        if refresh and settings["type"] == "openai_compatible":
            return self.provider(provider_name).list_models()
        return [str(model["name"]) for model in settings.get("models", []) if model.get("enabled", True)]