"""Tests: Grafik-Loader (Prefimage, Icon-Auflösung, Zip/Ordner-Extraktion)."""
from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from app.graphics.loader import graphic_path, icon_ref, parse_ref

# Keine gültige PNG, aber ausreichend für Pfad-/Ablage-Tests.
PNG_BYTES = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])


class _FakeMod:
    def __init__(self, name: str, source):
        self.name = name
        self.source = source


class GraphicsLoaderTests(unittest.TestCase):
    def test_parse_ref(self):
        self.assertEqual(
            parse_ref("__base__/graphics/icons/iron-plate.png"),
            ("base", "graphics/icons/iron-plate.png"),
        )
        self.assertEqual(
            parse_ref("__krastorio2__/icons/item.png"),
            ("krastorio2", "icons/item.png"),
        )
        self.assertEqual(parse_ref("relative/path.png"), ("base", "relative/path.png"))
        self.assertEqual(parse_ref(""), (None, None))

    def test_icon_ref_extraction(self):
        self.assertEqual(icon_ref({"icon": "a.png"}), "a.png")
        self.assertEqual(icon_ref({"icons": [{"icon": "b.png"}]}), "b.png")
        self.assertEqual(icon_ref({"other": 1}), "")

    def test_graphic_from_base_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data/base/graphics/icons").mkdir(parents=True)
            asset = root / "data/base/graphics/icons/iron-plate.png"
            asset.write_bytes(PNG_BYTES)
            out = graphic_path(root, [], {"icon": "__base__/graphics/icons/iron-plate.png"})
            self.assertIsNotNone(out)
            self.assertEqual(out.read_bytes(), PNG_BYTES)

    def test_graphic_from_mod_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mods_dir = root / "data/mods"
            mods_dir.mkdir(parents=True)
            archive = mods_dir / "mymod_1.0.0.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("mymod/icons/special.png", PNG_BYTES)
            mods = [_FakeMod("mymod", str(archive))]
            cache = root / "cache"
            out = graphic_path(root, mods, {"icon": "__mymod__/icons/special.png"}, cache_dir=cache)
            self.assertIsNotNone(out)
            self.assertEqual(out.read_bytes(), PNG_BYTES)

    def test_missing_asset_returns_none(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertIsNone(graphic_path(root, [], {"icon": "__base__/nope.png"}))

    def test_missing_icon_returns_none(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertIsNone(graphic_path(Path(temporary), [], {"name": "x"}))


if __name__ == "__main__":
    unittest.main()