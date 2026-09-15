"""Tests: Ollama-Modell-Erkennung gegen einen lokalen HTTP-Testserver (ohne Netz).

Simuliert GET /api/tags (lokale Modellliste) und prueft sowohl die
Ollama-Modul-Funktion als auch die ProviderManager-Ollama-Anbindung.
"""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.ai.manager import ProviderManager
from app.ai.ollama import list_models as ollama_list_models

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _TagsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/").endswith("/api/tags"):
            body = json.dumps({
                "models": [{"name": "qwen2.5-coder:7b"}, {"name": "gpt-oss:20b"}],
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # pragma: no cover
        pass


class OllamaProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _TagsHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_ollama_list_models_discovers_local_models(self):
        models = ollama_list_models(f"http://127.0.0.1:{self.port}", timeout=2)
        self.assertIn("qwen2.5-coder:7b", models)
        self.assertIn("gpt-oss:20b", models)

    def test_provider_manager_ollama_models_uses_configured_base_url(self):
        source = json.loads((PROJECT_ROOT / "config" / "ai_providers.json").read_text(encoding="utf-8"))
        source["providers"]["ollama"]["base_url"] = f"http://127.0.0.1:{self.port}"
        source["providers"]["ollama"]["enabled"] = True
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "ai_providers.json"
            config_path.write_text(json.dumps(source), encoding="utf-8")
            manager = ProviderManager(config_path)
            models = manager.ollama_models()
            self.assertIn("qwen2.5-coder:7b", models)


if __name__ == "__main__":
    unittest.main()