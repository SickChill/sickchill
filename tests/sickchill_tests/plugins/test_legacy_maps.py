from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.legacy_maps import DISCORD_MAP, NOTIFIER_LEGACY_MAPS, SLACK_MAP
from sickchill.plugins.settings import (
    migrate_extensions_notifiers_to_top_level,
    migrate_legacy_maps,
    read_notifier_section,
    sync_legacy_maps_to_settings,
    write_legacy_maps_from_settings,
)


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
        self.assertNotIn("extensions", cfg)

        discord = read_notifier_section(cfg, "discord")
        slack = read_notifier_section(cfg, "slack")
        self.assertEqual(discord.get("webhook"), "https://discord.example/hook")
        self.assertEqual(slack.get("webhook"), "https://slack.example/hook")
        self.assertEqual(cfg["NOTIFIERS"]["discord"]["webhook"], "https://discord.example/hook")

        # Idempotent
        self.assertFalse(migrate_legacy_maps(cfg, (DISCORD_MAP, SLACK_MAP)))

    def test_sync_populates_settings_from_notifiers(self):
        from sickchill import settings

        saved = {
            "USE_DISCORD": settings.USE_DISCORD,
            "DISCORD_WEBHOOK": settings.DISCORD_WEBHOOK,
            "USE_SLACK": settings.USE_SLACK,
            "SLACK_WEBHOOK": settings.SLACK_WEBHOOK,
        }
        self.addCleanup(lambda: [setattr(settings, k, v) for k, v in saved.items()])

        cfg = ConfigObj()
        cfg["NOTIFIERS"] = {
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
        settings.USE_DISCORD = False
        settings.DISCORD_WEBHOOK = ""
        settings.USE_SLACK = False
        settings.SLACK_WEBHOOK = ""
        sync_legacy_maps_to_settings(cfg, (DISCORD_MAP, SLACK_MAP))
        self.assertTrue(settings.USE_DISCORD)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://d")
        self.assertTrue(settings.USE_SLACK)
        self.assertEqual(settings.SLACK_WEBHOOK, "https://s")

    def test_sync_loads_whole_notifier_component_when_configured(self):
        """Configured NOTIFIERS[[id]] loads enable + params (needed for /config/notifications)."""
        from sickchill import settings
        from sickchill.plugins.legacy_maps import PLEX_MAP

        saved = {
            "USE_DISCORD": settings.USE_DISCORD,
            "DISCORD_WEBHOOK": settings.DISCORD_WEBHOOK,
            "USE_SLACK": settings.USE_SLACK,
            "SLACK_WEBHOOK": settings.SLACK_WEBHOOK,
            "USE_PLEX_SERVER": settings.USE_PLEX_SERVER,
            "PLEX_SERVER_HOST": settings.PLEX_SERVER_HOST,
        }
        self.addCleanup(lambda: [setattr(settings, k, v) for k, v in saved.items()])

        settings.USE_DISCORD = True
        settings.DISCORD_WEBHOOK = "https://stale"
        settings.PLEX_SERVER_HOST = None  # regression: Mako re.sub must not see None

        cfg = ConfigObj()
        cfg["NOTIFIERS"] = {
            "discord": {
                "enabled": False,
                "webhook": "https://from-config",
                "bot_name": "Nope",
                "avatar_url": "",
                "tts": False,
                "notify_snatch": False,
                "notify_download": False,
                "notify_subtitle_download": False,
            },
            "slack": {
                "enabled": True,
                "webhook": "https://new-slack",
                "notify_snatch": False,
                "notify_download": True,
                "notify_subtitledownload": False,
                "icon_emoji": ":ok:",
            },
            "plex": {
                "use_plex_server": False,
                "server_host": "http://plex:32400",
                "notify_onsnatch": False,
                "notify_ondownload": False,
                "notify_onsubtitledownload": False,
                "update_library": False,
                "server_token": "",
                "client_host": "",
                "server_username": "",
                "server_password": "",
                "use_plex_client": False,
                "client_username": "",
                "client_password": "",
                "server_https": False,
            },
        }
        sync_legacy_maps_to_settings(cfg, (DISCORD_MAP, SLACK_MAP, PLEX_MAP))
        self.assertFalse(settings.USE_DISCORD)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://from-config")
        self.assertTrue(settings.USE_SLACK)
        self.assertEqual(settings.SLACK_WEBHOOK, "https://new-slack")
        self.assertFalse(settings.USE_PLEX_SERVER)
        self.assertEqual(settings.PLEX_SERVER_HOST, "http://plex:32400")
        self.assertIsInstance(settings.PLEX_SERVER_HOST, str)

    def test_notifier_maps_cover_known_sections(self):
        ids = {m.plugin_id for m in NOTIFIER_LEGACY_MAPS}
        for required in ("discord", "slack", "telegram", "gotify", "kodi", "plex", "trakt"):
            self.assertIn(required, ids)

    def test_trakt_sync_bool_not_string_true(self):
        """Regression: ConfigObj 'True' must not land in settings.TRAKT_SYNC as str (breaks int())."""
        from sickchill import settings
        from sickchill.plugins.legacy_maps import TRAKT_MAP

        saved = {
            "TRAKT_SYNC": settings.TRAKT_SYNC,
            "TRAKT_SYNC_REMOVE": settings.TRAKT_SYNC_REMOVE,
        }
        self.addCleanup(lambda: [setattr(settings, k, v) for k, v in saved.items()])

        cfg = ConfigObj()
        cfg["NOTIFIERS"] = {
            "trakt": {
                "enabled": "True",
                "sync": "True",
                "sync_remove": "False",
                "method_add": "1",
                "timeout": "20",
                "default_indexer": "1",
            }
        }
        sync_legacy_maps_to_settings(cfg, (TRAKT_MAP,))
        self.assertIs(settings.TRAKT_SYNC, True)
        self.assertIs(settings.TRAKT_SYNC_REMOVE, False)
        # save_config does int(settings.TRAKT_SYNC)
        self.assertEqual(int(settings.TRAKT_SYNC), 1)
        out = ConfigObj()
        write_legacy_maps_from_settings(out, (TRAKT_MAP,))
        section = read_notifier_section(out, "trakt")
        self.assertIs(section.get("sync"), True)
        self.assertNotIn("extensions", out)

    def test_notifiers_and_clients_do_not_recreate_legacy_sections(self):
        """Migrated-only config must not grow empty legacy KODI/SABnzbd/Blackhole/General.metadata_* shells."""
        from sickchill.oldbeard.config import peek_setting_str
        from sickchill.plugins.legacy_maps import ALL_LEGACY_MAPS, CLIENT_SECTION_MAPS
        from sickchill.plugins.metadata.config import DEFAULT_PACKED, migrate_metadata_from_general, unpack_packed_config
        from sickchill.plugins.settings import migrate_client_maps, write_metadata_section

        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["NOTIFIERS"] = {
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

    def test_migrate_extensions_notifiers_to_top_level(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["extensions"] = {
            "notifiers": {
                "discord": {
                    "enabled": True,
                    "webhook": "https://from-extensions",
                    "bot_name": "ExtBot",
                }
            }
        }
        # Pre-existing NOTIFIERS key must not be overwritten when non-empty.
        cfg["NOTIFIERS"] = {"discord": {"webhook": "https://keep-me"}}

        self.assertTrue(migrate_extensions_notifiers_to_top_level(cfg))
        self.assertNotIn("extensions", cfg)
        discord = read_notifier_section(cfg, "discord")
        self.assertEqual(discord.get("webhook"), "https://keep-me")
        self.assertTrue(discord.get("enabled") in (True, "True", "1", 1) or str(discord.get("enabled")).lower() == "true")
        self.assertEqual(discord.get("bot_name"), "ExtBot")

        # Idempotent
        self.assertFalse(migrate_extensions_notifiers_to_top_level(cfg))

    def test_write_roundtrip_via_notifiers(self):
        from sickchill import settings

        saved = {
            "USE_DISCORD": settings.USE_DISCORD,
            "DISCORD_WEBHOOK": settings.DISCORD_WEBHOOK,
            "DISCORD_NAME": settings.DISCORD_NAME,
        }
        self.addCleanup(lambda: [setattr(settings, k, v) for k, v in saved.items()])

        settings.USE_DISCORD = True
        settings.DISCORD_WEBHOOK = "https://roundtrip"
        settings.DISCORD_NAME = "RT"
        out = ConfigObj()
        write_legacy_maps_from_settings(out, (DISCORD_MAP,))
        self.assertIn("NOTIFIERS", out)
        self.assertNotIn("extensions", out)
        self.assertEqual(out["NOTIFIERS"]["discord"]["webhook"], "https://roundtrip")

        settings.USE_DISCORD = False
        settings.DISCORD_WEBHOOK = ""
        sync_legacy_maps_to_settings(out, (DISCORD_MAP,))
        self.assertTrue(settings.USE_DISCORD)
        self.assertEqual(settings.DISCORD_WEBHOOK, "https://roundtrip")
