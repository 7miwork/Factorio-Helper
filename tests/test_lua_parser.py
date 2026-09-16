"""Tests: Lua-Data-Stage-Prototypen-Parser und dessen Einbindung in den Builder."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.factorio.lua_parser import (
    extract_prototypes,
    read_lua_prototypes,
    read_lua_prototypes_from_zip,
)
from app.knowledge.builder import build_knowledge_base
from app.knowledge.database import KnowledgeBase, database_path


SAMPLE = """
data:extend{
  {
    type = "recipe",
    name = "iron-plate",
    energy_required = 3.2,
    ingredients = {{"iron-ore", 1}},
    result = "iron-plate"
  },
  {
    type = "item",
    name = "iron-plate",
    icon = "__base__/graphics/icons/iron-plate.png",
    stack_size = 100
  },
  {
    type = "assembling-machine",
    name = "assembling-machine-1",
    icon = "__base__/graphics/entity/assembling-machine-1/assembling-machine-1.png",
    crafting_categories = {"crafting"}
  }
}
"""


class LuaParserTests(unittest.TestCase):
    def test_extract_prototypes_from_extend(self):
        records = extract_prototypes(SAMPLE, "base", "sample.lua")
        self.assertEqual(len(records), 3)
        types = {record.prototype_type for record in records}
        self.assertEqual(types, {"recipe", "item", "assembling-machine"})
        item = next(r for r in records if r.prototype_type == "item")
        recipe = next(r for r in records if r.prototype_type == "recipe")
        self.assertEqual(
            item.data.get("icon"),
            "__base__/graphics/icons/iron-plate.png",
        )
        self.assertNotIn("icon", recipe.data)

    def test_read_lua_prototypes_from_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "prototypes"
            (root / "item").mkdir(parents=True)
            (root / "item" / "iron.lua").write_text(SAMPLE, encoding="utf-8")
            records = read_lua_prototypes(root, "mymod")
            self.assertTrue(any(r.name == "assembling-machine-1" for r in records))
            self.assertTrue(all(r.source_mod == "mymod" for r in records))

    def test_read_lua_prototypes_from_zip(self):
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "mymod_1.0.0.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("mymod/data/prototypes/entity/boiler.lua", SAMPLE)
                handle.writestr("mymod/info.json", '{"name": "mymod"}')
            records = read_lua_prototypes_from_zip(archive, "mymod")
            self.assertTrue(any(r.name == "assembling-machine-1" for r in records))
            self.assertTrue(all(r.source_mod == "mymod" for r in records))
            self.assertTrue(any("data/prototypes" in r.source_file for r in records))


class LuaBuilderIntegrationTests(unittest.TestCase):
    def test_builder_indexes_native_lua_prototypes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data/base/prototypes/item").mkdir(parents=True)
            (root / "bin/x64").mkdir(parents=True)
            (root / "bin/x64/factorio.exe").touch()
            (root / "data/base/info.json").write_text('{"version": "2.0.18"}', encoding="utf-8")
            (root / "data/base/prototypes/item/iron.lua").write_text(SAMPLE, encoding="utf-8")
            count = build_knowledge_base(root, root)
            database = KnowledgeBase(database_path(root))
            try:
                records = database.find("item")
                self.assertTrue(any(r.name == "iron-plate" and "__base__" in str(r.data.get("icon", "")) for r in records))
            finally:
                database.close()
            self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()