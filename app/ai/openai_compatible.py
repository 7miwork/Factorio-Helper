import json
import os
from urllib.request import Request, urlopen


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key_env: str = "", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        self.timeout = timeout

    def _request(self, endpoint: str, payload: dict | None = None) -> dict:
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(f"{self.base_url}/{endpoint.lstrip('/')}", headers=headers, data=json.dumps(payload).encode() if payload is not None else None, method="POST" if payload is not None else "GET")
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_models(self) -> list[str]:
        return [str(model["id"]) for model in self._request("models").get("data", []) if model.get("id")]

    def complete(self, prompt: str, model: str) -> str:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        response = self._request("chat/completions", payload)
        return str(response["choices"][0]["message"]["content"])