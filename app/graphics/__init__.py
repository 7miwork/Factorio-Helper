"""Grafik-Loader: Prototyp-Referenzen zu Bilddateien auflösen und laden.

Factorio referenziert Grafiken über "__modname__/pfad/zur/datei.png". Dieses
Paket löst solche Referenzen gegen den Installationsordner und die installierten
Mods auf, extrahiert Bilddateien (aus Ordnern oder Mod-Zips) in einen Cache und
liefert einen direkt ladbaren Pfad zurück.

Hinweis: Vorerst werden PNG-Texel unterstützt (Tk kann PNG nativ anzeigen).
DDS-Texel werden erkannt, aber nicht geladen.
"""
from __future__ import annotations

import hashlib
import logging
import re
import shutil
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from ..utils import paths

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".png",)
# DDS wird derzeit nicht angezeigt; Dateien werden aber nicht als Fehler gemeldet.
KNOWN_EXTENSIONS = (".png", ".dds")

# "__modname__/rest/pfad.png"
PREFIX_RE = re.compile(r"^__(?P<mod>.+?)__/(?P<rel>.*)$")

DEFAULT_CACHE_DIR = paths.DATA_CACHE_DIR / "graphics"


def _default_cache_dir() -> Path:
    return DEFAULT_CACHE_DIR


def normalize_ref(ref: Optional[str]) -> str:
    """Normalisiert eine Grafik-Referenz (Schrägstriche, './'-Prefix)."""
    if not ref:
        return ""
    ref = str(ref).replace("\\", "/").strip()
    return ref.lstrip("./")


def parse_ref(ref: Optional[str]):
    """Zerlegt eine Referenz in (prefix, rel_path).

    "__base__/graphics/icons/iron-plate.png" -> ("base", "graphics/icons/iron-plate.png").
    Relative Pfade ohne Prefix werden auf "base" gemappt.
    """
    normalized = normalize_ref(ref)
    if not normalized:
        return None, None
    match = PREFIX_RE.match(normalized)
    if match:
        return match.group("mod"), match.group("rel")
    return "base", normalized