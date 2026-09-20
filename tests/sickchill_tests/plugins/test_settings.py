from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import Field, clear_registry, register
from sickchill.plugins.kinds.notifier import NotifierPlugin
from sickchill.plugins.settings import migrate_legacy_sections, read_notifier_section


class MigratorTests(unittest.TestCase):
    def tearDown(self):
        clear_registry()

    def test_clean_cut_and_idempotent(self):
        @register
        class Fake(NotifierPlugin):
            id = "fake"
            name = "Fake"
            legacy_sections = ("Discord",)
            schema = (Field(name="webhook", type="url", default="", legacy_keys=("webhook",)),)

        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Discord"] = {"webhook": "https://hooks.example/discord", "noise": "drop-me"}

        self.assertTrue(migrate_legacy_sections(cfg, [Fake]))
        section = read_notifier_section(cfg, Fake.id)
        self.assertEqual(section.get("webhook"), "https://hooks.example/discord")
        self.assertNotIn("Discord", cfg)
        self.assertNotIn("extensions", cfg)
        self.assertIn("NOTIFIERS", cfg)

        # Second migrate: no error, Discord stays gone
        self.assertFalse(migrate_legacy_sections(cfg, [Fake]))
        self.assertNotIn("Discord", cfg)
        self.assertEqual(read_notifier_section(cfg, Fake.id).get("webhook"), "https://hooks.example/discord")
