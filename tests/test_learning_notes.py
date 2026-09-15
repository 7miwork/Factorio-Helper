"""Tests: KI-Lern-Notizen (eigene Eingaben, die in den Planner-Kontext fließen)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.knowledge import context as ctx
from app.knowledge.database import KnowledgeBase


class LearningNotesTests(unittest.TestCase):
    def _db(self, path: Path) -> KnowledgeBase:
        return KnowledgeBase(path / "knowledge.db")

    def test_save_and_load_learning_notes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(ctx.paths, "ROOT", root):
                ctx.save_learning_notes("Nutze den Main Bus ab Phase 3.")
                self.assertEqual(ctx.load_learning_notes(), "Nutze den Main Bus ab Phase 3.")
                self.assertTrue((root / "data/learn/notes.md").is_file())

    def test_load_returns_empty_for_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(ctx.paths, "ROOT", Path(temporary)):
                self.assertEqual(ctx.load_learning_notes(), "")

    def test_planner_context_includes_learning_notes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            db_path = root / "knowledge.db"
            KnowledgeBase(db_path).close()  # initialisiert nur das Schema
            with patch.object(ctx.paths, "ROOT", root):
                db1 = KnowledgeBase(db_path)
                first = ctx.planner_context(db1)
                db1.close()
                self.assertNotIn("learning_notes", first)

                ctx.save_learning_notes("Halte Kraftwerke getrennt.")
                db2 = KnowledgeBase(db_path)
                second = ctx.planner_context(db2)
                db2.close()
                self.assertEqual(second["learning_notes"], "Halte Kraftwerke getrennt.")


if __name__ == "__main__":
    unittest.main()