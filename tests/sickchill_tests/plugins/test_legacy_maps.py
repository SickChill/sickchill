from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import PluginKind
from sickchill.plugins.legacy_maps import DISCORD_MAP, NOTIFIER_LEGACY_MAPS, SLACK_MAP
from sickchill.plugins.settings import migrate_legacy_maps, read_plugin_section, sync_legacy_maps_to_settings


class LegacyMapsMigratorTests(unittest.TestCase):
    def test_one_shot_migrates_multiple_notifier_sections(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Discord"] = {
            "use_discord": "1",
            "discord_webhook": "https://discord.example/hook",
            "discord_name": "SCBot",
            "discord_notify_snatch": "1",
            "discord_notify_download": "0",
            "discord_tts": "0",
            "discord_avatar_url": "https://img",
        }
        cfg["Slack"] = {
            "use_slack": "1",
            "slack_webhook": "https://slack.example/hook",
            "slack_notify_snatch": "0",
            "slack_notify_download": "1",
            "slack_notify_subtitledownload": "0",
            "slack_icon_emoji": ":ghost:",
        }

        self.assertTrue(migrate_legacy_maps(cfg, (DISCORD_MAP, SLACK_MAP)))
        self.assertNotIn("Discord", cfg)
        self.assertNotIn("Slack", cfg)

        discord = read_plugin_section(cfg, PluginKind.NOTIFIER, "discord")
        slack = read_plugin_section(cfg, PluginKind.NOTIFIER, "slack")
        self.assertEqual(discord.get("webhook"), "https://discord.example/hook")
        self.assertEqual(slack.get("webhook"), "https://slack.example/hook")

        # Idempotent
        self.assertFalse(migrate_legacy_maps(cfg, (DISCORD_MAP, SLACK_MAP)))

    def test_sync_populates_settings_from_extensions(self):
        from sickchill import settings

        cfg = ConfigObj()
        cfg["extensions"] = {
            "notifiers": {
                "discord": {
                    "enabled": True,
                    "webhook": "https://d",
                    "bot_name": "B",
                    "avatar_url": "",
                    "tts": False,
                    "notify_snatch": True,
                    "notify_download": False,
                    "notify_subtitle_download": False,
                },
                "slack": {
                    "enabled": True,
                    "webhook": "https://s",
                    "notify_snatch": False,
                    "notify_download": True,
                    "notify_subtitledownload": False,
                    "icon_emoji": ":x:",
                },
            }
        }
        settings.USE_DISCORD = False
        settings.DISCORD_WEBHOOK = ""
        settings.USE_SLACK = False
        settings.SLACK_WEBHOOK = ""
        sync_legacy_maps_to_settings(cfg, (DISCORD_MAP, SLACK_MAP))
        self.assertTrue(settings.USE_DISCORD)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://d")
        self.assertTrue(settings.USE_SLACK)
        self.assertEqual(settings.SLACK_WEBHOOK, "https://s")

    def test_notifier_maps_cover_known_sections(self):
        ids = {m.plugin_id for m in NOTIFIER_LEGACY_MAPS}
        for required in ("discord", "slack", "telegram", "gotify", "kodi", "plex", "trakt"):
            self.assertIn(required, ids)

    def test_trakt_sync_bool_not_string_true(self):
        """Regression: ConfigObj 'True' must not land in settings.TRAKT_SYNC as str (breaks int())."""
        from sickchill import settings
        from sickchill.plugins.legacy_maps import TRAKT_MAP
        from sickchill.plugins.settings import write_legacy_maps_from_settings

        cfg = ConfigObj()
        cfg["extensions"] = {
            "notifiers": {
                "trakt": {
                    "enabled": "True",
                    "sync": "True",
                    "sync_remove": "False",
                    "method_add": "1",
                    "timeout": "20",
                    "default_indexer": "1",
                }
            }
        }
        sync_legacy_maps_to_settings(cfg, (TRAKT_MAP,))
        self.assertIs(settings.TRAKT_SYNC, True)
        self.assertIs(settings.TRAKT_SYNC_REMOVE, False)
        # save_config does int(settings.TRAKT_SYNC)
        self.assertEqual(int(settings.TRAKT_SYNC), 1)
        out = ConfigObj()
        write_legacy_maps_from_settings(out, (TRAKT_MAP,))
        section = read_plugin_section(out, PluginKind.NOTIFIER, "trakt")
        self.assertIs(section.get("sync"), True)

    def test_extensions_and_clients_do_not_recreate_legacy_sections(self):
        """Migrated-only config must not grow empty legacy KODI/SABnzbd/Blackhole/General.metadata_* shells."""
        from sickchill.oldbeard.config import peek_setting_str
        from sickchill.plugins.legacy_maps import ALL_LEGACY_MAPS, CLIENT_SECTION_MAPS
        from sickchill.plugins.metadata.config import DEFAULT_PACKED, migrate_metadata_from_general, unpack_packed_config
        from sickchill.plugins.settings import migrate_client_maps, write_metadata_section

        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["extensions"] = {
            "notifiers": {
                "discord": {
                    "enabled": True,
                    "webhook": "https://discord.example/hook",
                    "bot_name": "SC",
                    "avatar_url": "",
                    "tts": False,
                    "notify_snatch": True,
                    "notify_download": False,
                    "notify_subtitle_download": False,
                }
            }
        }
        cfg["CLIENTS"] = {
            "blackhole": {"nzb_dir": "/nzb", "torrent_dir": "/torrent"},
            "sabnzbd": {"host": "http://sab:8080", "apikey": "key", "username": "sab"},
        }
        write_metadata_section(cfg, "kodi", unpack_packed_config("1|0|0|0|0|0|0|0|0|0"))
        cfg["General"] = {"root_dirs": "/tv"}

        self.assertFalse(migrate_legacy_maps(cfg, ALL_LEGACY_MAPS))
        self.assertFalse(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        self.assertFalse(migrate_metadata_from_general(cfg))

        for legacy in ("KODI", "Plex", "SABnzbd", "Blackhole", "NZBget", "TORRENT", "Discord"):
            self.assertNotIn(legacy, cfg)

        before_keys = set(cfg.keys())
        before_general = set(cfg["General"].keys())
        self.assertEqual(peek_setting_str(cfg, "KODI", "kodi_host", ""), "")
        self.assertEqual(peek_setting_str(cfg, "SABnzbd", "sab_host", ""), "")
        self.assertEqual(peek_setting_str(cfg, "Blackhole", "nzb_dir", ""), "")
        self.assertEqual(peek_setting_str(cfg, "General", "metadata_kodi", DEFAULT_PACKED), DEFAULT_PACKED)
        self.assertEqual(set(cfg.keys()), before_keys)
        self.assertEqual(set(cfg["General"].keys()), before_general)
        self.assertNotIn("metadata_kodi", cfg["General"])
        self.assertNotIn("KODI", cfg)
        self.assertNotIn("SABnzbd", cfg)
        self.assertNotIn("Blackhole", cfg)
