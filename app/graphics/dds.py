"""DDS(DirectDraw Surface)->PNG-Dekoder.

Factorio verwendet DDS-Texel (z. B. Spritesheets). Dieser Reader dekodiert die
haeufigste Variante – unkomprimierte 24/32-bit Bilder – und wandelt sie in ein
RGBA-PNG um (Standardbibliothek, ohne Pillow). Komprimierte (DXT-)Texel werden
erkannt und abgelehnt, da hier kein DXT-Decoder enthalten ist.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

DDS_MAGIC = b"DDS "

# Pixelformat-Typen fuer DXT-Kompression.
DXT_TYPES = frozenset((1, 3, 5))

# Pixelformat-Flag: 0x40 = festes BGRA-Layout (unabhaengig von Masken).
FLAG_FIXED_BGRA = 0x00000040

SGNR = b"\x89PNG\r\n\x1a\n"


class DdsError(ValueError):
    """Fehler beim Dekodieren einer DDS-Datei."""


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _channel(value: int, mask: int) -> int:
    """Extrahiert und normalisiert einen 8-bit-Farbkanal aus einem Bitmask."""
    if mask == 0:
        return 255
    shift = (mask & -mask).bit_length() - 1
    width = bin(mask).count("1")
    channel = (value & mask) >> shift
    if width < 8:
        channel <<= 8 - width
    return channel & 0xFF


def _write_png(width: int, height: int, rgba: bytes) -> bytes:
    def chunk(typ: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + typ + payload
                + struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    rows = bytearray()
    stride = width * 4
    for y in range(height):
        rows.append(0)  # Filtertyp None pro Zeile
        rows.extend(rgba[y * stride:(y + 1) * stride])
    idat = zlib.compress(bytes(rows))
    return SGNR + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def read_dds(path) -> tuple:
    """Liest eine DDS-Datei und liefert (png_bytes, width, height)."""
    data = Path(path).read_bytes()
    return decode_dds(data, str(path))


def decode_dds(data: bytes, source: str = "<dds>") -> tuple:
    """Dekodiert DDS-Bytes zu (png_bytes, width, height)."""
    if len(data) < 128 or data[:4] != DDS_MAGIC:
        raise DdsError(f"Keine gueltige DDS-Datei: {source}")

    height = _u32(data, 4)
    linear_size = _u32(data, 8)
    depth = _u32(data, 16)
    pixel_format = _u32(data, 20)
    pixel_flags = _u32(data, 84)
    r_mask, g_mask = _u32(data, 68), _u32(data, 72)
    b_mask, a_mask = _u32(data, 76), _u32(data, 80)

    if pixel_format in DXT_TYPES or depth <= 0:
        raise DdsError(f"DXT-komprimiert oder unbekanntes Format: {source}")

    bpp = depth // 8
    header_end = 128
    if len(data) < header_end + bpp:
        raise DdsError(f"Datei zu kurz fuer Pixeldaten: {source}")

    if linear_size > 0:
        width = linear_size // (height * bpp) if height else 0
    else:
        width = (len(data) - header_end) // (height * bpp) if height else 0
    if width <= 0 or height <= 0:
        raise DdsError(f"Unmoegliche Bildmasse {width}x{height}: {source}")

    raw = data[header_end:header_end + width * height * bpp]
    fixed_bgra = bool(pixel_flags & FLAG_FIXED_BGRA) or (not (r_mask or g_mask or b_mask))

    rgba = bytearray(width * height * 4)
    pos = 0
    for y in range(height):
        for x in range(width):
            start = (y * width + x) * bpp
            if bpp == 4:
                value = int.from_bytes(raw[start:start + 4], "little")
                if fixed_bgra:
                    b0, g0, r0, a0 = raw[start], raw[start + 1], raw[start + 2], raw[start + 3]
                else:
                    r0 = _channel(value, r_mask)
                    g0 = _channel(value, g_mask)
                    b0 = _channel(value, b_mask)
                    a0 = _channel(value, a_mask) if a_mask else 255
            else:  # 3 BPP (24-bit RGB)
                value = int.from_bytes(raw[start:start + 3], "little")
                r0 = _channel(value, r_mask)
                g0 = _channel(value, g_mask)
                b0 = _channel(value, b_mask)
                a0 = 255
            rgba[pos] = r0
            rgba[pos + 1] = g0
            rgba[pos + 2] = b0
            rgba[pos + 3] = a0
            pos += 4

    return _write_png(width, height, bytes(rgba)), width, height