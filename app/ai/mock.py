import json


class MockProvider:
    def list_models(self) -> list[str]:
        return ["builtin"]

    def complete(self, prompt: str, model: str = "builtin") -> str:
        return json.dumps({"name": "Mock Starter Base", "description": "Deterministic test plan", "layout_strategy": "expandable", "production": [], "machines": [], "inputs": [], "outputs": [], "constraints": []})