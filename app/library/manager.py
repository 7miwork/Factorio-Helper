import json
from pathlib import Path

from app.blueprint.encoder import encode
from app.blueprint.validator import validate


class LibraryManager:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, slug: str, blueprint: dict, metadata: dict | None = None) -> Path:
        issues = validate(blueprint)
        if issues:
            raise ValueError("Cannot save invalid blueprint: " + "; ".join(issue.reason for issue in issues))
        folder = self.root / slug
        folder.mkdir(parents=True, exist_ok=True)
        label = blueprint["blueprint"].get("label", slug)
        (folder / "blueprint.json").write_text(json.dumps(blueprint, indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / "blueprint.txt").write_text(encode(blueprint), encoding="utf-8")
        details = {"slug": slug, "name": label, "entities": len(blueprint["blueprint"].get("entities", [])), **(metadata or {})}
        (folder / "metadata.json").write_text(json.dumps(details, indent=2, ensure_ascii=False), encoding="utf-8")
        readme = metadata.get("readme") if metadata else None
        if not readme:
            readme = f"# {label}\n\nBlueprint mit {details['entities']} Entities.\n"
        (folder / "README.md").write_text(readme, encoding="utf-8")
        return folder

    def list(self) -> list[dict]:
        entries = []
        for metadata_path in sorted(self.root.glob("*/metadata.json")):
            try:
                entries.append(json.loads(metadata_path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return entries