"""Phase 4 search provider plugins — PROVIDERS migrate / apply / write."""

from __future__ import annotations

import logging
import unittest

from configobj import ConfigObj

from sickchill import settings
from sickchill.oldbeard.config import peek_setting_bool, peek_setting_str
from sickchill.plugins.api import PluginKind, clear_registry
from sickchill.plugins.manager import PluginManager
from sickchill.plugins.providers import config as providers_config, load_first_party_providers
from sickchill.plugins.providers.config import (
    apply_providers_from_cfg,
    migrate_provider_sections,
    write_providers_to_cfg,
)
from sickchill.plugins.settings import ensure_provider_section, read_provider_section, write_provider_section


class ProviderPluginTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        self.manager = PluginManager()
        self._saved = {
            "providerList": settings.providerList,
            "newznab_provider_list": settings.newznab_provider_list,
            "torrent_rss_provider_list": settings.torrent_rss_provider_list,
            "PROVIDER_ORDER": settings.PROVIDER_ORDER,
            "NEWZNAB_DATA": settings.NEWZNAB_DATA,
            "CFG": settings.CFG,
            "ENCRYPTION_VERSION": settings.ENCRYPTION_VERSION,
            "USE_NZBS": settings.USE_NZBS,
            "USE_TORRENTS": settings.USE_TORRENTS,
        }
        self._saved_full_applied = providers_config._providers_full_settings_applied
        settings.providerList = []
        settings.newznab_provider_list = []
        settings.torrent_rss_provider_list = []
        settings.PROVIDER_ORDER = []
        settings.NEWZNAB_DATA = ""
        settings.ENCRYPTION_VERSION = 0
        providers_config._providers_full_settings_applied = False

    def tearDown(self):
        clear_registry()
        for key, value in self._saved.items():
            setattr(settings, key, value)
        providers_config._providers_full_settings_applied = self._saved_full_applied

    def test_migrate_abnormal_legacy_section_to_providers(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["ABNORMAL"] = {
            "abnormal": True,
            "abnormal_username": "user1",
            "abnormal_password": "secret",
            "abnormal_minseed": 2,
        }
        cfg["General"] = {"provider_order": "abnormal", "use_torrents": 1}

        with self.assertLogs("sickchill.plugins.providers", level=logging.INFO) as logs:
            self.assertTrue(migrate_provider_sections(cfg))

        self.assertTrue(any("ABNORMAL" in line and "PROVIDERS[[abnormal]]" in line for line in logs.output))
        self.assertNotIn("ABNORMAL", cfg)
        self.assertIn("General", cfg)
        self.assertEqual(cfg["General"].get("provider_order"), "abnormal")

        section = read_provider_section(cfg, "abnormal")
        self.assertTrue(section.get("enabled") in (True, "True", "true", 1, "1"))
        self.assertEqual(section.get("username"), "user1")
        self.assertEqual(section.get("password"), "secret")
        self.assertEqual(str(section.get("minseed")), "2")

    def test_migrate_empty_legacy_section_silent_not_mutated(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["ABNORMAL"] = {}
        cfg["General"] = {"use_torrents": 1}

        # Empty scrub: silent (no INFO) and not mutated
        self.assertFalse(migrate_provider_sections(cfg))
        self.assertNotIn("ABNORMAL", cfg)
        self.assertIn("General", cfg)
        # Idempotent second pass
        self.assertFalse(migrate_provider_sections(cfg))

    def test_migrate_newznab_blob_to_providers(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        # name|url|key|categories|enabled|search_mode|search_fallback|enable_daily|enable_backlog
        blob = "My Custom|https://nzb.example/|abc123|5030,5040|1|episode|0|1|0"
        cfg["Newznab"] = {"newznab_data": blob}
        cfg["General"] = {"use_nzbs": 1}

        with self.assertLogs("sickchill.plugins.providers", level=logging.INFO) as logs:
            self.assertTrue(migrate_provider_sections(cfg))

        self.assertTrue(any("Newznab" in line and "type=newznab" in line for line in logs.output))
        self.assertNotIn("Newznab", cfg)
        self.assertIn("General", cfg)

        section = read_provider_section(cfg, "my_custom")
        self.assertEqual(section.get("type"), "newznab")
        self.assertEqual(section.get("name"), "My Custom")
        self.assertEqual(section.get("url"), "https://nzb.example/")
        self.assertEqual(section.get("key"), "abc123")
        self.assertTrue(section.get("enabled") in (True, "True", "true", 1, "1"))

    def test_apply_sets_enabled_and_username_from_providers(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(
            cfg,
            "abnormal",
            {"enabled": True, "username": "from_providers", "password": "pw", "minseed": 3},
        )

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider

        provider = AbnormalProvider()
        provider.enabled = False
        provider.username = None
        provider.password = None
        provider.minseed = 0

        settings.providerList = [provider]
        settings.newznab_provider_list = []
        settings.torrent_rss_provider_list = []
        settings.PROVIDER_ORDER = ["abnormal"]

        apply_providers_from_cfg(cfg)

        self.assertTrue(provider.enabled)
        self.assertEqual(provider.username, "from_providers")
        self.assertEqual(provider.password, "pw")
        self.assertEqual(provider.minseed, 3)

    def test_write_providers_does_not_recreate_abnormal_legacy(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["ABNORMAL"] = {"abnormal": 0}
        cfg["General"] = {"provider_order": "abnormal"}

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider

        fake = AbnormalProvider()
        fake.enabled = True
        fake.username = "u"
        fake.password = "p"
        fake.minseed = 1
        fake.minleech = 0
        fake.enable_daily = True
        fake.enable_backlog = True

        settings.providerList = [fake]
        settings.newznab_provider_list = []
        settings.torrent_rss_provider_list = []
        settings.PROVIDER_ORDER = ["abnormal"]
        write_providers_to_cfg(cfg)

        self.assertNotIn("ABNORMAL", cfg)
        self.assertIn("PROVIDERS", cfg)
        self.assertIn("abnormal", cfg["PROVIDERS"])
        self.assertTrue(cfg["PROVIDERS"]["abnormal"].get("enabled") in (True, "True", "true", 1, "1"))
        self.assertEqual(cfg["PROVIDERS"]["abnormal"].get("username"), "u")
        self.assertIn("General", cfg)

    def test_peek_does_not_create_empty_legacy_provider_sections(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["PROVIDERS"] = {"abnormal": {"enabled": True, "username": "x"}}
        cfg["General"] = {"root_dirs": "/tv"}

        before = set(cfg.keys())
        self.assertEqual(peek_setting_str(cfg, "ABNORMAL", "abnormal_username", ""), "")
        self.assertFalse(peek_setting_bool(cfg, "ABNORMAL", "abnormal", False))
        self.assertEqual(set(cfg.keys()), before)
        self.assertNotIn("ABNORMAL", cfg)

    def test_jackett_sc_categories_path_preserved(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cats = "5000,5030,5040,5045,5050,5060,5070"
        write_provider_section(
            cfg,
            "jackett_sc",
            {
                "enabled": True,
                "custom_url": "http://127.0.0.1:9117",
                "api_key": "testkey",
                "categories": cats,
                "indexer": "all",
            },
        )

        from sickchill.oldbeard.providers.jackett import Provider as JackettProvider

        jackett = JackettProvider()
        settings.providerList = [jackett]
        settings.newznab_provider_list = []
        settings.torrent_rss_provider_list = []
        settings.PROVIDER_ORDER = ["jackett_sc"]

        apply_providers_from_cfg(cfg)

        self.assertEqual(jackett.get_id(), "jackett_sc")
        self.assertTrue(jackett.uses_configurable_categories)
        self.assertEqual(jackett.categories, cats)
        self.assertEqual(jackett.custom_url, "http://127.0.0.1:9117")
        self.assertTrue(jackett.enabled)

        write_providers_to_cfg(cfg)
        self.assertNotIn("JACKETT_SC", cfg)
        written = read_provider_section(cfg, "jackett_sc")
        self.assertEqual(written.get("categories"), cats)
        self.assertEqual(written.get("custom_url"), "http://127.0.0.1:9117")

    def test_manager_get_provider_without_enabled_gate(self):
        load_first_party_providers()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        ensure_provider_section(cfg, "abnormal")
        cfg["PROVIDERS"]["abnormal"]["enabled"] = False
        cfg["PROVIDERS"]["abnormal"]["username"] = "disabled_user"

        self.manager._cfg = cfg
        self.manager.discover()
        plugin = self.manager.get(PluginKind.PROVIDER, "abnormal")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "abnormal")
        self.assertEqual(plugin.ctx.get("username"), "disabled_user")
        # instance() default also skips enable gate for PROVIDER
        plugin2 = self.manager.instance(PluginKind.PROVIDER, "abnormal")
        self.assertIsNotNone(plugin2)

    def test_load_first_party_registers_jackett_sc(self):
        load_first_party_providers()
        self.manager.discover()
        classes = self.manager.classes(PluginKind.PROVIDER)
        ids = {cls.id for cls in classes}
        self.assertIn("abnormal", ids)
        self.assertIn("jackett_sc", ids)
        self.assertNotIn("jackett", ids)  # module name is jackett; id is jackett_sc
        self.assertTrue(all(cls.kind == PluginKind.PROVIDER for cls in classes))
        self.assertGreaterEqual(len(ids), 50)

    def test_ensure_read_write_provider_section(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        section = ensure_provider_section(cfg, "eztv")
        section["enabled"] = True
        write_provider_section(cfg, "eztv", {"enabled": False, "minseed": 1})
        self.assertEqual(read_provider_section(cfg, "eztv").get("minseed"), 1)
        self.assertIn("PROVIDERS", cfg)
        self.assertNotIn("extensions", cfg)

    def test_apply_enabled_only_skips_disabled_credentials(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(
            cfg,
            "abnormal",
            {"enabled": False, "username": "secret_user", "password": "secret_pw", "minseed": 7},
        )

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider

        provider = AbnormalProvider()
        provider.enabled = True
        provider.username = "init_user"
        provider.password = "init_pw"
        provider.minseed = 0

        settings.providerList = [provider]
        settings.PROVIDER_ORDER = ["abnormal"]

        apply_providers_from_cfg(cfg, enabled_only=True)

        self.assertFalse(provider.enabled)
        self.assertEqual(provider.username, "init_user")
        self.assertEqual(provider.password, "init_pw")
        self.assertEqual(provider.minseed, 0)
        self.assertEqual(settings.PROVIDER_ORDER, [])
        self.assertFalse(providers_config._providers_full_settings_applied)

        apply_providers_from_cfg(cfg, enabled_only=False)

        self.assertFalse(provider.enabled)
        self.assertEqual(provider.username, "secret_user")
        self.assertEqual(provider.password, "secret_pw")
        self.assertEqual(provider.minseed, 7)
        self.assertTrue(providers_config._providers_full_settings_applied)

    def test_apply_normalizes_provider_order_to_enabled_existing(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(cfg, "abnormal", {"enabled": True, "username": "u"})
        write_provider_section(cfg, "eztv", {"enabled": False})

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider
        from sickchill.oldbeard.providers.eztv import Provider as EztvProvider

        abnormal = AbnormalProvider()
        eztv = EztvProvider()
        settings.providerList = [abnormal, eztv]
        settings.PROVIDER_ORDER = ["eztv:0", "abnormal", "missing_provider", "abnormal:1"]

        apply_providers_from_cfg(cfg, enabled_only=True)

        self.assertTrue(abnormal.enabled)
        self.assertFalse(eztv.enabled)
        self.assertEqual(settings.PROVIDER_ORDER, ["abnormal"])

    def test_sorted_provider_list_enabled_order_then_disabled_alpha(self):
        from sickchill.oldbeard.providers import sorted_provider_list
        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider
        from sickchill.oldbeard.providers.eztv import Provider as EztvProvider
        from sickchill.oldbeard.providers.nyaa import Provider as NyaaProvider

        alpha = AbnormalProvider()
        alpha.enabled = True
        alpha.name = "Zulu Enabled"
        beta = EztvProvider()
        beta.enabled = True
        beta.name = "Alpha Enabled"
        disabled_b = NyaaProvider()
        disabled_b.enabled = False
        disabled_b.name = "Bravo Disabled"
        # Second disabled via a duplicate-style fake using torrentrss custom
        from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider

        disabled_a = TorrentRssProvider("Alpha Disabled", "https://a.example/rss", "", "title")
        disabled_a.enabled = False

        settings.USE_TORRENTS = True
        settings.USE_NZBS = True
        settings.providerList = [alpha, beta, disabled_b]
        settings.torrent_rss_provider_list = [disabled_a]
        settings.newznab_provider_list = []
        # Priority: Zulu before Alpha among enabled
        settings.PROVIDER_ORDER = [alpha.get_id(), beta.get_id()]

        ordered = sorted_provider_list()
        ids = [p.get_id() for p in ordered]
        self.assertEqual(ids[:2], [alpha.get_id(), beta.get_id()])
        disabled_ids = ids[2:]
        disabled_names = [p.name for p in ordered[2:]]
        self.assertEqual(disabled_names, sorted(disabled_names, key=str.lower))
        self.assertEqual(set(disabled_ids), {disabled_a.get_id(), disabled_b.get_id()})

    def test_write_providers_prunes_orphan_sections(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(cfg, "abnormal", {"enabled": True, "username": "u"})
        write_provider_section(
            cfg,
            "orphan_custom",
            {"type": "newznab", "name": "Orphan", "url": "https://orphan.example/", "key": "k", "enabled": False},
        )

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider

        provider = AbnormalProvider()
        provider.enabled = True
        provider.username = "u"
        settings.providerList = [provider]
        settings.newznab_provider_list = []
        settings.torrent_rss_provider_list = []
        settings.PROVIDER_ORDER = ["abnormal"]
        providers_config._providers_full_settings_applied = True

        write_providers_to_cfg(cfg)

        self.assertIn("abnormal", cfg["PROVIDERS"])
        self.assertNotIn("orphan_custom", cfg["PROVIDERS"])

    def test_write_preserves_disabled_credentials_when_not_fully_loaded(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(
            cfg,
            "abnormal",
            {"enabled": False, "username": "keep_me", "password": "keep_pw", "minseed": 9},
        )

        from sickchill.oldbeard.providers.abnormal import Provider as AbnormalProvider

        provider = AbnormalProvider()
        provider.enabled = False
        provider.username = None
        provider.password = None
        provider.minseed = 0
        settings.providerList = [provider]
        settings.PROVIDER_ORDER = []
        providers_config._providers_full_settings_applied = False

        write_providers_to_cfg(cfg)

        section = read_provider_section(cfg, "abnormal")
        self.assertEqual(section.get("username"), "keep_me")
        self.assertEqual(section.get("password"), "keep_pw")
        self.assertEqual(str(section.get("minseed")), "9")
        self.assertTrue(section.get("enabled") in (False, "False", "false", 0, "0"))


if __name__ == "__main__":
    unittest.main()
