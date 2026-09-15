import json
from urllib.request import Request, urlopen


def list_models(base_url: str = "http://localhost:11434", timeout: float = 3.0) -> list[str]:
    """Return locally installed Ollama model names without downloading anything."""
    request = Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [str(model["name"]) for model in payload.get("models", []) if model.get("name")]