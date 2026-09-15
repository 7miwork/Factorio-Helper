"""Tests: Mod-Scan aus data/mods (Spezifikation) und strukturierte Dependency-Parsung."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.factorio.mod_scanner import (
    mod_to_dict,
    parse_dependencies,
    parse_dependency,
    scan_mods,
)


class ModScannerDataModsTests(unittest.TestCase):
    def _make_installation(self, path: Path, mods_subdir: str) -> Path:
        (path / "data/base").mkdir(parents=True)
        (path / "data/base/info.json").write_text(json.dumps({"version": "2.0.18"}), encoding="utf-8")
        mods_dir = path / mods_subdir
        mods_dir.mkdir(parents=True)
        mod_list = mods_dir / "mod-list.json"
        mod_list.write_text(
            json.dumps({"mods": [{"name": "krastorio2", "enabled": True},
                                 {"name": "aai-containers", "enabled": False}]}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(mods_dir / "Krastorio2_1.0.3.zip", "w") as archive:
            archive.writestr(
                "Krastorio2_1.0.3/info.json",
                json.dumps({
                    "name": "krastorio2", "version": "1.0.3", "title": "Krastorio 2",
                    "dependencies": ["base >= 2.0.0", "? optional-mod"],
                }),
            )
        return mods_dir

    def test_scan_mods_from_data_mods(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._make_installation(root, "data/mods")
            found = scan_mods(root)
            self.assertEqual(len(found), 1)
            mod = found[0]
            self.assertEqual(mod.name, "krastorio2")
            self.assertEqual(mod.version, "1.0.3")
            self.assertTrue(mod.enabled)
            self.assertEqual(mod.dependencies, ("base", "optional-mod"))
            # Die (falls vorhandene) Installation bleibt daneben gültig.
            self.assertTrue((root / "data/base/info.json").is_file())

    def test_scan_mods_marks_disabled_mod(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mods_dir = self._make_installation(root, "data/mods")
            with zipfile.ZipFile(mods_dir / "AAI-Containers_1.1.0.zip", "w") as archive:
                archive.writestr(
                    "aai-containers/info.json",
                    json.dumps({"name": "aai-containers", "version": "1.1.0",
                                "title": "AAI Containers", "dependencies": []}),
                )
            found = {mod.name: mod for mod in scan_mods(root)}
            self.assertFalse(found["aai-containers"].enabled)

    def test_mod_to_dict_shape(self):
        with tempfile.TemporaryDirectory() as temporary:
            mods_dir = self._make_installation(Path(temporary), "mods")
            mod = scan_mods(Path(temporary))[0]
            payload = mod_to_dict(mod)
            self.assertEqual(payload["version"], "1.0.3")
            self.assertEqual(payload["dependencies"], ["base", "optional-mod"])

    def test_parse_dependency_forms(self):
        self.assertEqual(parse_dependency("base >= 2.0.0"),
                         {"raw": "base >= 2.0.0", "name": "base", "optional": False,
                          "hidden": False, "operator": ">=", "version": "2.0.0"})
        self.assertTrue(parse_dependency("? optional-mod")["optional"])
        self.assertTrue(parse_dependency("(?) hidden-mod")["hidden"])
        self.assertTrue(parse_dependency("~ maybe-mod")["optional"])
        self.assertTrue(parse_dependencies(["base"]))


if __name__ == "__main__":
    unittest.main()