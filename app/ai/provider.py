from typing import Protocol


class AIProvider(Protocol):
    def list_models(self) -> list[str]: ...

    def complete(self, prompt: str, model: str) -> str: ...