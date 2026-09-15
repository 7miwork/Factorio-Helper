"""Grafik-Loader: Dateipfade zu den Grafikassets einer Installation auflösen."""
from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from . import (
    SUPPORTED_EXTENSIONS,
    normalize_ref,
    parse_ref,
)

logger = logging.getLogger(__name__)


def _mods_index(mods) -> dict:
    """name -> Mod. Nimmt ModInfo-Objekte mit .name und .source."""
    return {mod.name: mod for mod in (mods or [])}


def _source_location(install_path: Path, mods_index: dict, prefix: str) -> Optional[Path]:
    """Liefert die Quelle (data/base bzw. Mod-Source) für einen __prefix__."""
    if prefix == "base":
        base_dir = Path(install_path) / "data" / "base"
        return base_dir if base_dir.is_dir() else None
    mod = mods_index.get(prefix)
    if mod is None:
        return None
    source = Path(mod.source)
    return source if source.exists() else None


def _cached_target(cache_dir: Path, rel_path: str, suffix: str = ".png") -> Path:
    """Bestimmt einen sicheren Cache-Dateinamen für eine Asset-Referenz."""
    digest = hashlib.sha1(rel_path.encode("utf-8", "replace")).hexdigest()[:16]
    return cache_dir / f"{digest}{suffix}"


def extract_asset(source: Path, rel_path: str, cache_dir: Path) -> Optional[Path]:
    """Liefert einen tatsächlichen Dateipfad für ein Asset (Zip/Ordner) im Cache."""
    rel_path = normalize_ref(rel_path).lstrip("/")
    cache_dir.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        candidate = source / rel_path
        return candidate if candidate.is_file() else None

    if source.suffix.lower() == ".zip":
        target = _cached_target(cache_dir, rel_path)
        try:
            with ZipFile(source) as archive:
                entry = _find_zip_entry(archive.namelist(), rel_path)
                if entry is None:
                    return None
                with archive.open(entry) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            return target
        except (OSError, ValueError, KeyError):
            logger.warning("Asset-Extraktion fehlgeschlagen: %s", rel_path, exc_info=True)
            return None

    return None


def _find_zip_entry(names, rel_path: str) -> Optional[str]:
    """Findet einen Zip-Eintrag für einen (mod-relativen) Pfad.

    Zips legen Assets häufig als "<modname>/<rel>" ab; geprüft wird exakt sowie
    als Endung "/<rel>" und "<modname>/<rel>".
    """
    rel_norm = rel_path.replace("\\", "/").lstrip("/")
    entries = {name.replace("\\", "/"): name for name in names}
    if rel_norm in entries:
        return entries[rel_norm]
    for entry in entries:
        if entry.endswith("/" + rel_norm):
            return entries[entry]
    return None


def icon_ref(prototype_data: dict) -> str:
    """Extrahiert die Icon-Referenz aus Prototypendaten.

    Berücksichtigt "icon" sowie das "icons"-Feld (erster gültiger Eintrag).
    """
    if not isinstance(prototype_data, dict):
        return ""
    ref = prototype_data.get("icon")
    if ref:
        return normalize_ref(ref)
    icons = prototype_data.get("icons")
    if isinstance(icons, list):
        for item in icons:
            if isinstance(item, dict) and item.get("icon"):
                return normalize_ref(item["icon"])
    return ""


def graphic_path(
    install_path,
    mods,
    prototype_data,
    cache_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Löst die Grafik für einen Prototypen-Datensatz zu einer Cache-Datei auf.

    Gibt die Datei (PNG) zurück, die direkt angezeigt werden kann, oder None,
    wenn keine (lesbare) Grafik existiert (z. B. DDS oder fehlendes Icon).
    """
    ref = icon_ref(prototype_data)
    if not ref:
        return None
    prefix, rel = parse_ref(ref)
    if rel is None:
        return None

    source = _source_location(Path(install_path), _mods_index(mods), prefix)
    if source is None:
        return None

    asset = extract_asset(source, rel, cache_dir or _cache_dir())
    if asset is None:
        return None
    if asset.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return None
    return asset


def _cache_dir() -> Path:
    from . import DEFAULT_CACHE_DIR

    return DEFAULT_CACHE_DIR