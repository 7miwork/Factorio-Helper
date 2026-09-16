"""Tests: DDS->PNG-Dekoder (unkomprimierte 32-bit Texturen)."""
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from app.graphics.dds import DdsError, decode_dds, read_dds
from app.graphics.preview import png_dimensions


def make_uncompressed_rgba_dds(width: int, height: int, rgba: bytes) -> bytes:
    """Baut eine unkomprimierte 32-bit DDS mit RGBA-Masken zusammen."""
    linear = width * height * 4
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, height)
    struct.pack_into("<I", header, 8, linear)
    struct.pack_into("<I", header, 12, 0)          # flags
    struct.pack_into("<I", header, 16, 32)         # depth
    struct.pack_into("<I", header, 20, 0)          # pixelFormat = unkomprimiert
    struct.pack_into("<I", header, 68, 0x000000FF)  # R-Maske
    struct.pack_into("<I", header, 72, 0x0000FF00)  # G-Maske
    struct.pack_into("<I", header, 76, 0x00FF0000)  # B-Maske
    struct.pack_into("<I", header, 80, 0xFF000000)  # A-Maske
    struct.pack_into("<I", header, 84, 0)           # pixelFormatFlags
    return bytes(header) + rgba


class DdsDecoderTests(unittest.TestCase):
    def test_decode_uncompressed_rgba(self):
        rgba = bytes([
            255, 0, 0, 255,   # rot
            0, 255, 0, 255,   # gruen
            0, 0, 255, 255,   # blau
            10, 20, 30, 40,
        ])
        png, width, height = decode_dds(make_uncompressed_rgba_dds(2, 2, rgba), "test.dds")
        self.assertEqual((width, height), (2, 2))
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_read_dds_and_png_dimensions(self):
        rgba = bytes([255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 255])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tex.dds"
            path.write_bytes(make_uncompressed_rgba_dds(2, 2, rgba))
            png, width, height = read_dds(path)
            self.assertEqual((width, height), (2, 2))
            self.assertEqual(png_dimensions(path), (None, None))  # DDS besitzt kein PNG-IHDR
            png_path = Path(temporary) / "tex.png"
            png_path.write_bytes(png)
            self.assertEqual(png_dimensions(png_path), (2, 2))

    def test_dxt_compression_rejected(self):
        header = bytearray(128)
        header[0:4] = b"DDS "
        struct.pack_into("<I", header, 4, 1)
        struct.pack_into("<I", header, 16, 32)
        struct.pack_into("<I", header, 20, 1)  # DXT1
        with self.assertRaises(DdsError):
            decode_dds(bytes(header) + b"\x00", "dxt.dds")

    def test_junk_rejected(self):
        with self.assertRaises(DdsError):
            decode_dds(b"xxxx", "junk.dds")


if __name__ == "__main__":
    unittest.main()