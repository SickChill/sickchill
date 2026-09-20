from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import Field, clear_registry, register
from sickchill.plugins.kinds.notifier import NotifierPlugin
from sickchill.plugins.settings import migrate_legacy_sections, read_notifier_section, remove_retired_notifier_sections


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

    def test_remove_retired_notifier_sections(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Growl"] = {"use_growl": "0", "growl_host": ""}
        cfg["Boxcar2"] = {"use_boxcar2": "0"}
        cfg["Pushalot"] = {"use_pushalot": "0"}
        cfg["NMA"] = {"use_nma": "0"}
        cfg["NOTIFIERS"] = {
            "growl": {"enabled": False},
            "discord": {"enabled": True, "webhook": "https://keep"},
        }
        cfg["extensions"] = {"notifiers": {"pushalot": {"enabled": False}, "slack": {"enabled": True}}}

        self.assertTrue(remove_retired_notifier_sections(cfg))
        for section in ("Growl", "Boxcar2", "Pushalot", "NMA"):
            self.assertNotIn(section, cfg)
        self.assertNotIn("growl", cfg["NOTIFIERS"])
        self.assertIn("discord", cfg["NOTIFIERS"])
        self.assertEqual(cfg["NOTIFIERS"]["discord"].get("webhook"), "https://keep")
        self.assertNotIn("pushalot", cfg["extensions"]["notifiers"])
        self.assertIn("slack", cfg["extensions"]["notifiers"])

        self.assertFalse(remove_retired_notifier_sections(cfg))
