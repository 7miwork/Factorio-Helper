"""Tests: GUI-Paket ist importierbar (Spezifikationsstruktur app/gui)."""
from __future__ import annotations

import unittest


class GuiImportTests(unittest.TestCase):
    def test_gui_modules_import(self):
        import app.main
        import app.gui.ai_tab
        import app.gui.factorio_tab
        import app.gui.generator_tab
        import app.gui.knowledge_tab
        import app.gui.library_tab
        import app.gui.main_window
        import app.gui.mods_tab
        import app.gui.settings_tab
        self.assertTrue(hasattr(app.gui.main_window, "MainWindow"))

    def test_gui_module_spec_tabs(self):
        import app.gui.factorio_tab as f
        import app.gui.mods_tab as m
        import app.gui.ai_tab as a
        import app.gui.settings_tab as s
        for module, cls_name in ((f, "FactorioTab"), (m, "ModsTab"),
                                 (a, "AISettingsTab"), (s, "SettingsTab")):
            self.assertTrue(hasattr(module, cls_name))


if __name__ == "__main__":
    unittest.main()