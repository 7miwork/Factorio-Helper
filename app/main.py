"""Factorio AI Blueprint Generator – Einstiegspunkt (CLI + GUI).

Start der GUI:
    python -m app.main

CLI-Beispiele:
    python -m app.main scan "<factorio-Installation>"
    python -m app.main models
    python -m app.main providers
    python -m app.main knowledge "<factorio-Installation>"
    python -m app.main validate blueprint.txt
    python -m app.main generate requirements.txt

Die grafische Oberfläche ist in app/gui/ in getrennten Tabs organisiert.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.blueprint.decoder import decode
from app.blueprint.validator import validate
from app.ai.manager import ProviderManager
from app.factorio.detector import detect_installation
from app.factorio.mod_scanner import mod_to_dict, scan_mods
from app.knowledge.builder import build_knowledge_base
from app.utils import paths
from app.workflow import generate_from_requirements

PROJECT_ROOT = paths.ROOT
CONFIG_PATH = PROJECT_ROOT / "config" / "ai_providers.json"


def scan(factorio_path: str) -> dict:
    """Scannt Installation (Version) und Mods; liefert ein strukturiertes Dict."""
    installation = detect_installation(factorio_path)
    return {
        "path": str(installation.path),
        "version": installation.version or "unknown",
        "mods": [mod_to_dict(mod) for mod in scan_mods(installation.path)],
    }


def launch_gui() -> None:
    import tkinter as tk
    from app.gui.main_window import MainWindow

    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="app.main",
        description="Factorio AI Blueprint Generator",
    )
    parser.add_argument(
        "command", nargs="?", default="gui",
        choices=("gui", "scan", "models", "providers", "knowledge", "validate", "generate"),
        help="CLI-Kommando (Standard: gui)",
    )
    parser.add_argument("path", nargs="?", help="Factorio-Installations- bzw. Dateipfad")
    args = parser.parse_args(argv)

    if args.command == "scan":
        if not args.path:
            parser.error("scan erfordert einen Factorio-Installationspfad")
        print(json.dumps(scan(args.path), indent=2, ensure_ascii=False))

    elif args.command == "models":
        manager = ProviderManager(CONFIG_PATH)
        for name, setting in manager.config.get("providers", {}).items():
            for model in setting.get("models", []):
                print(f"{name} ({setting.get('type')}): {model['name']}")

    elif args.command == "providers":
        manager = ProviderManager(CONFIG_PATH)
        for name, setting in manager.config.get("providers", {}).items():
            state = "enabled" if setting.get("enabled") else "disabled"
            print(f"{name}: {state} ({setting.get('type')})")

    elif args.command == "knowledge":
        if not args.path:
            parser.error("knowledge erfordert einen Factorio-Installationspfad")
        print(f"Importierte Prototypen: {build_knowledge_base(args.path, PROJECT_ROOT)}")

    elif args.command == "validate":
        if not args.path:
            parser.error("validate erfordert eine Blueprint-JSON- oder Blueprint-String-Datei")
        content = Path(args.path).read_text(encoding="utf-8").strip()
        blueprint = json.loads(content) if content.startswith("{") else decode(content)
        issues = validate(blueprint)
        if issues:
            print("Blueprint invalid")
            for issue in issues:
                print(f"- {issue.reason}" + (f": {issue.suggestion}" if issue.suggestion else ""))
            raise SystemExit(1)
        print("Blueprint valid")

    elif args.command == "generate":
        if not args.path:
            parser.error("generate erfordert eine Anforderungs-Textdatei")
        requirements = Path(args.path).read_text(encoding="utf-8")
        print(json.dumps(generate_from_requirements(requirements, PROJECT_ROOT), indent=2, ensure_ascii=False))

    else:
        launcher = launch_gui()


if __name__ == "__main__":
    main()