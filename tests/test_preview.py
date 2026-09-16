"""Tests: Grafik-Vorschau (PNG/DDS, optionale Pillow-Skalierung)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.graphics import preview
from app.graphics.preview import png_dimensions, preview_bytes
from tests.test_dds import make_uncompressed_rgba_dds


class PreviewTests(unittest.TestCase):
    def test_preview_bytes_from_png(self):
        rgba = bytes([255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 255])
        with tempfile.TemporaryDirectory() as temporary:
            # über DDS-Dekoder ein gültiges PNG erzeugen
            from app.graphics.dds import decode_dds
            png, _, _ = decode_dds(make_uncompressed_rgba_dds(2, 2, rgba), "t.dds")
            png_path = Path(temporary) / "t.png"
            png_path.write_bytes(png)
            result, width, height = preview_bytes(png_path, 1.0)
            self.assertEqual((width, height), (2, 2))
            self.assertEqual(result, png)
            self.assertEqual(png_dimensions(png_path), (2, 2))

    def test_preview_bytes_from_dds(self):
        rgba = bytes([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160])
        with tempfile.TemporaryDirectory() as temporary:
            dds_path = Path(temporary) / "t.dds"
            dds_path.write_bytes(make_uncompressed_rgba_dds(2, 2, rgba))
            result, width, height = preview_bytes(dds_path, 1.0)
            self.assertEqual((width, height), (2, 2))
            self.assertTrue(result.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_unsupported_format(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                preview_bytes(Path(temporary) / "a.gif", 1.0)

    def test_description(self):
        self.assertEqual(preview.description(1.0), "1x")
        self.assertEqual(preview.description(2.0), "2x")
        self.assertEqual(preview.description(0.75), "75 %")


if __name__ == "__main__":
    unittest.main()