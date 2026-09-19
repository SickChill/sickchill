from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import Field, PluginKind, clear_registry, register
from sickchill.plugins.kinds.notifier import NotifierPlugin
from sickchill.plugins.manager import PluginManager


class ManagerTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        self.manager = PluginManager()

        @register
        class Fake(NotifierPlugin):
            id = "fake"
            name = "Fake"
            schema = (Field(name="webhook", type="url", default=""),)

        self.Fake = Fake

    def tearDown(self):
        clear_registry()

    def test_discover_register_and_lazy_instance(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        self.manager._cfg = cfg
        self.manager.discover()

        classes = self.manager.classes(PluginKind.NOTIFIER)
        self.assertEqual(len(classes), 1)
        self.assertIs(classes[0], self.Fake)
        self.assertEqual(self.manager.enabled(PluginKind.NOTIFIER), [])
        self.assertIsNone(self.manager.instance(PluginKind.NOTIFIER, "fake"))

        cfg["extensions"] = {"notifiers": {"fake": {"enabled": True, "webhook": "https://example.test"}}}
        first = self.manager.instance(PluginKind.NOTIFIER, "fake")
        second = self.manager.instance(PluginKind.NOTIFIER, "fake")
        self.assertIsNotNone(first)
        self.assertIs(first, second)
        self.assertEqual(self.manager.enabled(PluginKind.NOTIFIER), [first])

    def test_context_isolation(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["extensions"] = {
            "notifiers": {
                "fake": {"enabled": True, "webhook": "https://a.test"},
                "other": {"enabled": True, "webhook": "https://b.test"},
            }
        }

        @register
        class Other(NotifierPlugin):
            id = "other"
            name = "Other"
            schema = (Field(name="webhook", type="url", default=""),)

        self.manager._cfg = cfg
        self.manager.discover()
        fake = self.manager.instance(PluginKind.NOTIFIER, "fake")
        other = self.manager.instance(PluginKind.NOTIFIER, "other")
        assert fake is not None and other is not None
        self.assertEqual(fake.ctx.get("webhook"), "https://a.test")
        self.assertNotIn("https://b.test", fake.ctx.settings.values())
        fake.ctx.update(webhook="https://updated.test")
        self.assertEqual(cfg["extensions"]["notifiers"]["fake"]["webhook"], "https://updated.test")
        self.assertEqual(cfg["extensions"]["notifiers"]["other"]["webhook"], "https://b.test")

    def test_import_does_not_load_providers(self):
        import ast
        from pathlib import Path

        # manager.py itself must not import providers. (Importing the sickchill package
        # still pulls providers via tv.py circular imports — that is outside this module.)
        path = Path(__file__).resolve().parents[3] / "sickchill" / "plugins" / "manager.py"
        tree = ast.parse(path.read_text())
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        self.assertFalse(
            any(name.startswith("sickchill.oldbeard.providers") or name == "sickchill.oldbeard.providers" for name in imported),
            msg=f"manager.py imports providers: {imported}",
        )
