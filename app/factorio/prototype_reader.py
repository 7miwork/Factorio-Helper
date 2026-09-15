import json
from pathlib import Path
import zipfile

from app.knowledge.entities import Prototype


KNOWN_TYPES = {"item", "entity", "recipe", "technology", "fluid", "resource", "module"}


def read_json_prototypes(path: str | Path, source_mod: str = "unknown") -> list[Prototype]:
    """Read exported prototype JSON; Factorio's native data stage remains Lua."""
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    prototypes = []
    collections = payload.items() if isinstance(payload, dict) else [("unknown", payload)]
    for prototype_type, values in collections:
        normalized_type = prototype_type.removesuffix("s")
        if normalized_type not in KNOWN_TYPES or not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict) and value.get("name"):
                prototypes.append(Prototype(str(value["name"]), normalized_type, source_mod, str(source), value))
    return prototypes


def read_prototypes(root: str | Path, source_mod: str = "unknown") -> list[Prototype]:
    result = []
    for path in sorted(Path(root).rglob("*.json")):
        if path.name == "info.json" or "__pycache__" in path.parts:
            continue
        try:
            result.extend(read_json_prototypes(path, source_mod))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return result


def read_zip_prototypes(path: str | Path, source_mod: str = "unknown") -> list[Prototype]:
    result = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".json") or name.endswith("/info.json"):
                continue
            try:
                payload = json.loads(archive.read(name).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            collections = payload.items() if isinstance(payload, dict) else []
            for prototype_type, values in collections:
                normalized_type = prototype_type.removesuffix("s")
                if normalized_type not in KNOWN_TYPES or not isinstance(values, list):
                    continue
                for value in values:
                    if isinstance(value, dict) and value.get("name"):
                        result.append(Prototype(str(value["name"]), normalized_type, source_mod, f"{path}:{name}", value))
    return result