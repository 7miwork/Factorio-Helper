import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from app.factorio.detector import detect_installation
from app.factorio.mod_scanner import scan_mods
from app.factorio.prototype_reader import read_json_prototypes, read_zip_prototypes
from app.knowledge.database import KnowledgeBase
from app.blueprint.decoder import decode
from app.blueprint.encoder import encode
from app.blueprint.generator import generate
from app.blueprint.validator import validate, validate_against_knowledge
from app.layout.engine import arrange
from app.library.book import create_book
from app.library.manager import LibraryManager
from app.knowledge.context import planner_context
from app.knowledge.entities import Prototype
from app.workflow import generate_from_requirements
from app.knowledge.production import calculate_requirements
from app.knowledge.recipes import parse_recipe
from app.ai.mock import MockProvider
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.planner import ProductionPlanner
from app.ai.manager import ProviderManager


class PhaseOneTests(unittest.TestCase):
    def test_detects_version_and_mod_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data/base").mkdir(parents=True)
            (root / "bin/x64").mkdir(parents=True)
            (root / "bin/x64/factorio.exe").touch()
            (root / "data/base/info.json").write_text(json.dumps({"version": "2.0.18"}), encoding="utf-8")
            mods = root / "mods"
            mods.mkdir()
            (mods / "mod-list.json").write_text(json.dumps({"mods": [{"name": "test-mod", "enabled": True}]}), encoding="utf-8")
            with zipfile.ZipFile(mods / "test-mod_1.2.3.zip", "w") as archive:
                archive.writestr("test-mod_1.2.3/info.json", json.dumps({"name": "test-mod", "version": "1.2.3", "title": "Test Mod", "dependencies": ["base >= 2.0", "? optional-mod"]}))
            installation = detect_installation(root)
            self.assertEqual(installation.version, "2.0.18")
            found = scan_mods(root)
            self.assertEqual(found[0].version, "1.2.3")
            self.assertEqual(found[0].dependencies, ("base", "optional-mod"))

    def test_imports_json_prototypes_into_sqlite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "prototypes.json"
            source.write_text(json.dumps({"items": [{"name": "iron-plate", "stack_size": 100}], "recipes": [{"name": "iron-plate"}]}), encoding="utf-8")
            prototypes = read_json_prototypes(source, "base")
            database = KnowledgeBase(root / "knowledge.db")
            try:
                self.assertEqual(database.add(prototypes), 2)
                self.assertEqual(database.count(), 2)
                self.assertEqual(database.find("item")[0].name, "iron-plate")
            finally:
                database.close()

    def test_blueprint_encode_decode_roundtrip_and_validation(self):
        blueprint = generate({"name": "Starter", "machines": [{"name": "assembling-machine-1", "recipe": "iron-gear-wheel"}]})
        self.assertEqual(decode(encode(blueprint)), blueprint)
        self.assertEqual(validate(blueprint), [])
        invalid = {"blueprint": {"item": "blueprint", "entities": [{"entity_number": 1, "name": "x", "position": {"x": "bad", "y": 0}}]}}
        self.assertTrue(validate(invalid))

    def test_layout_strategies_create_deterministic_positions(self):
        machines = [{"name": "assembling-machine-1"} for _ in range(5)]
        compact = arrange(machines, "compact", columns=2)
        expandable = arrange(machines, "expandable", columns=2)
        self.assertEqual(compact[2]["position"], {"x": 0, "y": 2})
        self.assertGreater(expandable[1]["position"]["x"], compact[1]["position"]["x"])

    def test_mock_and_openai_compatible_provider(self):
        self.assertEqual(json.loads(MockProvider().complete("test"))["name"], "Mock Starter Base")

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self): return json.dumps({"choices": [{"message": {"content": "reply"}}]}).encode()

        with patch("app.ai.openai_compatible.urlopen", return_value=Response()):
            self.assertEqual(OpenAICompatibleProvider("http://localhost/v1").complete("hello", "local"), "reply")

    def test_production_planner_validates_structured_mock_plan(self):
        config = Path(r"Z:\Codes\My Projects\Factorio Helper\config\ai_providers.json")
        plan = ProductionPlanner(__import__("app.ai.manager", fromlist=["ProviderManager"]).ProviderManager(config)).create_plan({}, "starter base")
        self.assertEqual(plan["layout_strategy"], "expandable")

    def test_library_saves_blueprint_files_and_book(self):
        blueprint = generate({"name": "Starter", "machines": [{"name": "assembling-machine-1"}]})
        with tempfile.TemporaryDirectory() as temporary:
            folder = LibraryManager(Path(temporary)).save("01-starter", blueprint, {"purpose": "early base"})
            self.assertTrue((folder / "blueprint.txt").is_file())
            self.assertEqual(LibraryManager(Path(temporary)).list()[0]["purpose"], "early base")
            book = create_book("Test Book", [blueprint])
            self.assertEqual(book["blueprint_book"]["blueprints"][0]["index"], 1)

    def test_planner_context_contains_typed_prototypes(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = KnowledgeBase(Path(temporary) / "knowledge.db")
            try:
                database.add([Prototype("iron-plate", "item", "base", "export.json", {"stack_size": 100})])
                self.assertEqual(planner_context(database)["item"][0]["name"], "iron-plate")
            finally:
                database.close()

    def test_generate_workflow_writes_library_output(self):
        source_root = Path(r"Z:\Codes\My Projects\Factorio Helper")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "config/ai_providers.json").write_text((source_root / "config/ai_providers.json").read_text(encoding="utf-8"), encoding="utf-8")
            result = generate_from_requirements("starter base", root, "test-output")
            self.assertTrue((root / "blueprints/test-output/blueprint.txt").is_file())
            self.assertTrue(result["blueprint_string"].startswith("0"))

    def test_recipe_parser_calculates_raw_production_inputs(self):
        gear = parse_recipe({"name": "iron-gear-wheel", "ingredients": [{"name": "iron-plate", "amount": 2}], "result": "iron-gear-wheel", "energy_required": 0.5})
        requirements = calculate_requirements([gear], "iron-gear-wheel", 60)
        self.assertEqual(requirements["iron-plate"], 2)

    def test_blueprint_validator_checks_knowledge_base(self):
        blueprint = generate({"name": "Checked", "machines": [{"name": "unknown-machine", "recipe": "unknown-recipe"}]})
        prototypes = [
            Prototype("assembling-machine-1", "entity", "base", "export.json", {"crafting_categories": ["crafting"]}),
            Prototype("iron-gear-wheel", "recipe", "base", "export.json", {"category": "crafting"}),
        ]
        issues = validate_against_knowledge(blueprint, prototypes)
        self.assertTrue(any("Unknown entity" in issue.reason for issue in issues))

    def test_reads_json_prototypes_from_zip_mod(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "mod.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mod/data.json", json.dumps({"items": [{"name": "mod-item"}]}))
            self.assertEqual(read_zip_prototypes(archive_path, "mod")[0].name, "mod-item")

    def test_configures_optional_remote_providers_without_network(self):
        manager = ProviderManager(Path(r"Z:\Codes\My Projects\Factorio Helper\config\ai_providers.json"))
        self.assertIn("openrouter", manager.config["providers"])
        self.assertIn("huggingface", manager.config["providers"])
        self.assertEqual(manager.models("mock"), ["builtin"])


if __name__ == "__main__":
    unittest.main()