from pathlib import Path
import json

from app.blueprint.encoder import encode


def create_book(label: str, blueprints: list[dict]) -> dict:
    entries = []
    for index, blueprint in enumerate(blueprints, start=1):
        root = blueprint.get("blueprint", {})
        entries.append({"index": index, "blueprint": root})
    return {"blueprint_book": {"item": "blueprint-book", "label": label, "blueprints": entries, "active_index": 0, "version": 562949953421312}}


def save_book(path: str | Path, book: dict) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.with_suffix(".json").write_text(json.dumps(book, indent=2, ensure_ascii=False), encoding="utf-8")
    destination.with_suffix(".txt").write_text(encode(book), encoding="utf-8")
    return destination