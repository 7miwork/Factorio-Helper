from pathlib import Path

from app.factorio.detector import detect_installation
from app.factorio.mod_scanner import scan_mods
from app.factorio.prototype_reader import read_prototypes, read_zip_prototypes
from app.factorio.lua_parser import read_lua_prototypes, read_lua_prototypes_from_zip
from app.knowledge.database import KnowledgeBase, database_path
from app.knowledge.entities import Prototype


def build_knowledge_base(installation_path: str | Path, project_root: str | Path) -> int:
    installation = detect_installation(installation_path)
    mods = scan_mods(installation.path)
    records = [Prototype(mod.name, "mod", mod.name, mod.source, {"name": mod.name, "version": mod.version, "title": mod.title, "dependencies": list(mod.dependencies), "enabled": mod.enabled}) for mod in mods]
    records.extend(read_prototypes(installation.path / "data", "base"))
    # Native Lua-Data-Stage (Echt-Daten inkl. Icons), falls vorhanden.
    records.extend(read_lua_prototypes(installation.path / "data" / "base" / "prototypes", "base"))
    for mod in mods:
        if Path(mod.source).is_dir():
            records.extend(read_prototypes(mod.source, mod.name))
            records.extend(read_lua_prototypes(Path(mod.source) / "data" / "prototypes", mod.name))
        elif Path(mod.source).suffix.lower() == ".zip":
            records.extend(read_zip_prototypes(mod.source, mod.name))
            records.extend(read_lua_prototypes_from_zip(mod.source, mod.name))
    database = KnowledgeBase(database_path(project_root))
    try:
        return database.add(records)
    finally:
        database.close()