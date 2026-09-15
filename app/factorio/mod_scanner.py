"""Mod-Scanner: erkennt installierte Mods, Versionen und Abhängigkeiten.

Die Installation kann ihre Mods im Spezifikationspfad <factorio>/data/mods oder
im klassischen <factorio>/mods ablegen – beide werden unterstützt. Gelesen wird
aus gezippten Mods (ModInfo_<version>.zip) sowie aus nicht-gezippten
Mod-Ordnern. Die aktivierten Mods werden aus mod-list.json entnommen.

Die Abhängigkeiten werden sowohl als Namenstupel (ModInfo.dependencies) als auch
strukturiert (parse_dependency/parse_dependencies) bereitgestellt.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import zipfile

# Spezifizierte Faktorio-Datenstruktur (zusätzlich zu einem klassischen "mods").
MOD_DIR_NAMES = ("data/mods", "mods")

# Operatoren für Versions-Abhängigkeiten (für die strukturierte Parsung).
_OPERATOR_PATTERN = re.compile(r"(~>|>=|<=|!=|==|=|<|>|~)")


@dataclass(frozen=True)
class ModInfo:
    name: str
    version: str
    title: str
    dependencies: tuple[str, ...]
    enabled: bool
    source: str


def _dependency_name(value: str) -> str | None:
    value = re.sub(r"^[!?~<>= ]+", "", value.strip())
    return value.split()[0] if value else None


def parse_dependency(dependency: str) -> dict:
    """Parst eine Abhängigkeit in Name, Operator und Version (optional/hidden)."""
    dependency = (dependency or "").strip()
    if not dependency:
        return {
            "raw": "", "name": "", "optional": False, "hidden": False,
            "operator": None, "version": None,
        }
    prefix = ""
    text = dependency
    match = re.match(r"^(\(\?\)|\?|~)\s*", dependency)
    if match:
        prefix = match.group(1)
        text = dependency[match.end():]
    optional = "?" in prefix or "~" in prefix
    hidden = prefix == "(?)"
    name = text.strip()
    operator = None
    version = None
    op_match = _OPERATOR_PATTERN.search(text)
    if op_match:
        name = text[: op_match.start()].strip()
        operator = op_match.group(1)
        version = text[op_match.end():].strip() or None
    return {
        "raw": dependency, "name": name, "optional": optional, "hidden": hidden,
        "operator": operator, "version": version,
    }


def parse_dependencies(dependencies) -> list:
    if not isinstance(dependencies, list):
        return []
    return [parse_dependency(item) for item in dependencies if isinstance(item, str)]


def _find_mods_dir(root: Path) -> Path | None:
    for relative in MOD_DIR_NAMES:
        candidate = root / relative
        if candidate.is_dir():
            return candidate
    return None


def _read_info(path: Path) -> dict:
    if path.is_dir():
        info_path = path / "info.json"
        return json.loads(info_path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(path) as archive:
        candidates = [
            name for name in archive.namelist()
            if name.endswith("/info.json") or name == "info.json"
        ]
        if not candidates:
            raise ValueError(f"No info.json in {path.name}")
        return json.loads(archive.read(candidates[0]).decode("utf-8"))


def scan_mods(installation_path: str | Path) -> list[ModInfo]:
    """Scannt eine Installation auf Mods und gibt list[ModInfo] zurück."""
    root = Path(installation_path).expanduser().resolve()
    mods_path = _find_mods_dir(root) or (root / "mods")

    enabled: dict = {}
    for mod_list_path in (
        mods_path / "mod-list.json",
        root / "mod-list.json",
    ):
        if not mod_list_path.is_file():
            continue
        try:
            items = json.loads(mod_list_path.read_text(encoding="utf-8")).get("mods", [])
            enabled = {
                item["name"]: item.get("enabled", True)
                for item in items if isinstance(item, dict)
            }
            break
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            continue

    results: list[ModInfo] = []
    for path in sorted(mods_path.iterdir() if mods_path.is_dir() else []):
        if not (path.is_dir() or path.suffix.lower() == ".zip"):
            continue
        if path.name.startswith("."):
            continue
        try:
            info = _read_info(path)
        except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile):
            continue
        dependencies = tuple(
            name for name in (_dependency_name(dep) for dep in info.get("dependencies", []))
            if name
        )
        results.append(
            ModInfo(
                name=str(info.get("name", path.stem)),
                version=str(info.get("version", "unknown")),
                title=str(info.get("title", info.get("name", path.stem))),
                dependencies=dependencies,
                enabled=enabled.get(str(info.get("name", path.stem)), True),
                source=str(path),
            )
        )
    return results


def mod_to_dict(mod: ModInfo) -> dict:
    result = asdict(mod)
    result["dependencies"] = list(mod.dependencies)
    return result