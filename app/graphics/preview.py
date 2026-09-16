"""Grafik-Vorschau: Laedt PNG/DDS und liefert PNG-Bytes in einer Zielgroesse.

Ohne Pillow wird nur die Originalgroesse geliefert (PNG unveraendert, DDS via
eigenem Decoder). Mit Pillow (optional) koennen mehrere Zoomstufen/Skalierungen
erzeugt werden.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

from . import dds

try:  # optional
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:  # noqa: BLE001
    PIL_AVAILABLE = False

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SUPPORTED_EXTENSIONS = (".png", ".dds")


def png_dimensions(path) -> tuple:
    """Liest Breite/Hoehe eines PNG aus dem IHDR (ohne Bild zu dekodieren)."""
    try:
        with open(path, "rb") as handle:
            header = handle.read(24)
        if header[:8] == PNG_SIGNATURE and header[12:16] == b"IHDR":
            return struct.unpack_from(">II", header, 16)
    except OSError:
        pass
    return (None, None)


def _source_bytes(path: Path):
    """Laedt Originalbild einer PNG/DDS-Datei; liefert (png_bytes, w, h)."""
    ext = path.suffix.lower()
    if ext == ".png":
        width, height = png_dimensions(path)
        return path.read_bytes(), width, height
    if ext == ".dds":
        return dds.read_dds(path)
    raise ValueError(f"Nicht unterstuetztes Grafikformat: {ext or path.name}")


def preview_bytes(path, scale: float = 1.0, max_dim: int = 256) -> tuple:
    """Liefert (png_bytes, width, height) einer Grafik in der gewuenschten Skala."""
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Nicht unterstuetztes Grafikformat: {path.suffix or path.name}")

    if not PIL_AVAILABLE:
        png_bytes, width, height = _source_bytes(path)
        if scale != 1.0:
            raise ValueError("Skalierung erfordert Pillow (python -m pip install pillow)")
        return png_bytes, width, height

    png_bytes, width, height = _source_bytes(path)
    with Image.open(io.BytesIO(png_bytes)) as image:
        image = image.convert("RGBA")
        target_w = max(1, round(width * scale)) if width else image.width
        target_h = max(1, round(height * scale)) if height else image.height
        target_w = min(target_w, max_dim)
        target_h = min(target_h, max_dim)
        if (target_w, target_h) != (image.width, image.height):
            image = image.resize((target_w, target_h), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return buffer.getvalue(), target_w, target_h


def description(scale: float) -> str:
    """Kurze Beschreibung der Skalierung (fuer die GUI)."""
    if scale < 1.0:
        return f"{int(scale * 100)} %"
    if scale == int(scale):
        return f"{int(scale)}x"
    return f"{scale:g}x"