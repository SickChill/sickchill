from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import PluginKind, clear_registry
from sickchill.plugins.manager import PluginManager
from sickchill.plugins.notifiers.compat import sync_discord_settings_from_cfg
from sickchill.plugins.settings import migrate_legacy_sections, read_notifier_section


class DiscordNotifierPluginTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        import sickchill.plugins.notifiers.discord as discord_mod

        self.Discord = discord_mod.DiscordNotifier
        # Re-register after clear
        from sickchill.plugins.api import register

        register(self.Discord)
        self.manager = PluginManager()

    def tearDown(self):
        clear_registry()

    def test_migrates_discord_section_and_deletes_legacy(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Discord"] = {
            "use_discord": "1",
            "discord_webhook": "https://discord.example/hook",
            "discord_name": "SCBot",
            "discord_notify_snatch": "1",
            "discord_notify_download": "0",
            "discord_tts": "0",
            "discord_avatar_url": "https://example.test/a.png",
        }
        self.assertTrue(migrate_legacy_sections(cfg, [self.Discord]))
        self.assertNotIn("Discord", cfg)
        self.assertNotIn("extensions", cfg)
        section = read_notifier_section(cfg, "discord")
        self.assertTrue(section.get("enabled") in (True, "1", 1, "True") or str(section.get("enabled")).lower() in {"1", "true"})
        # migrator stores raw config values
        self.assertEqual(section.get("webhook"), "https://discord.example/hook")
        self.assertEqual(section.get("bot_name"), "SCBot")
        self.assertFalse(migrate_legacy_sections(cfg, [self.Discord]))

    def test_enabled_instance_uses_notifiers(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["NOTIFIERS"] = {
            "discord": {
                "enabled": True,
                "webhook": "https://discord.example/hook",
                "bot_name": "SCBot",
                "notify_snatch": True,
                "notify_download": False,
                "tts": False,
                "avatar_url": "",
                "notify_subtitle_download": False,
            }
        }
        self.manager._cfg = cfg
        self.manager.discover()
        plugin = self.manager.instance(PluginKind.NOTIFIER, "discord")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.ctx.get("webhook"), "https://discord.example/hook")
        self.assertEqual(len(self.manager.enabled(PluginKind.NOTIFIER)), 1)

    def test_sync_settings_from_notifiers(self):
        from sickchill import settings
        from sickchill.plugins.bootstrap import sync_all_plugin_runtime_settings

        cfg = ConfigObj()
        cfg["NOTIFIERS"] = {
            "discord": {
                "enabled": True,
                "webhook": "https://hooks.example/x",
                "bot_name": "Bot",
                "avatar_url": "https://img",
                "tts": True,
                "notify_snatch": True,
                "notify_download": True,
                "notify_subtitle_download": False,
            }
        }
        # Simulate empty legacy load wiping globals, then one-shot sync from NOTIFIERS.
        settings.USE_DISCORD = False
        settings.DISCORD_WEBHOOK = ""
        settings.DISCORD_NAME = ""
        sync_all_plugin_runtime_settings(cfg)
        self.assertTrue(settings.USE_DISCORD)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://hooks.example/x")
        self.assertEqual(settings.DISCORD_NAME, "Bot")

    def test_sync_before_save_preserves_notifiers(self):
        """Regression: save_config after migrate must not write empty settings over NOTIFIERS."""
        from sickchill import settings
        from sickchill.plugins.notifiers.compat import write_discord_settings_to_cfg

        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Discord"] = {
            "use_discord": "1",
            "discord_webhook": "https://discord.example/hook",
            "discord_name": "SCBot",
            "discord_notify_snatch": "1",
            "discord_notify_download": "1",
            "discord_tts": "0",
            "discord_avatar_url": "https://example.test/a.png",
        }
        migrate_legacy_sections(cfg, [self.Discord])
        self.assertNotIn("Discord", cfg)
        sync_discord_settings_from_cfg(cfg)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://discord.example/hook")
        # Emulate save path: write from synced settings back into a fresh ConfigObj
        out = ConfigObj()
        out.indent_type = "  "
        write_discord_settings_to_cfg(out)
        section = read_notifier_section(out, "discord")
        self.assertEqual(section.get("webhook"), "https://discord.example/hook")
        enabled = section.get("enabled")
        self.assertTrue(enabled is True or str(enabled).lower() in {"1", "true", "yes", "on"})
        self.assertNotIn("extensions", out)
