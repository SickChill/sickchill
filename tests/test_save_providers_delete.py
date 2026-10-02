"""Custom Newznab/Torrent RSS deletes must persist on saveProviders."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from configobj import ConfigObj

from sickchill import settings
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider
from sickchill.plugins.providers import config as providers_config
from sickchill.plugins.settings import write_provider_section
from sickchill.views.config.providers import ConfigProviders


class SaveProvidersDeleteTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            "newznab_provider_list": settings.newznab_provider_list,
            "torrent_rss_provider_list": settings.torrent_rss_provider_list,
            "NEWZNAB_DATA": settings.NEWZNAB_DATA,
            "PROVIDER_ORDER": settings.PROVIDER_ORDER,
            "providerList": settings.providerList,
            "CFG": settings.CFG,
        }
        self._saved_full_applied = providers_config._providers_full_settings_applied
        settings.providerList = []
        settings.PROVIDER_ORDER = []
        settings.CFG = None
        settings.newznab_provider_list = [
            NewznabProvider("KeepMe", "https://keep.example/", key="k1", categories="5030"),
            NewznabProvider("Jackett", "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/", key="secret", categories="5000"),
        ]
        settings.torrent_rss_provider_list = [
            TorrentRssProvider("RssKeep", "https://rss.example/feed", "", "title"),
            TorrentRssProvider("RssDrop", "https://rss.example/drop", "", "title"),
        ]
        providers_config._providers_full_settings_applied = True

    def tearDown(self):
        settings.newznab_provider_list = self._saved["newznab_provider_list"]
        settings.torrent_rss_provider_list = self._saved["torrent_rss_provider_list"]
        settings.NEWZNAB_DATA = self._saved["NEWZNAB_DATA"]
        settings.PROVIDER_ORDER = self._saved["PROVIDER_ORDER"]
        settings.providerList = self._saved["providerList"]
        settings.CFG = self._saved["CFG"]
        providers_config._providers_full_settings_applied = self._saved_full_applied

    def _handler(self, body: dict):
        handler = ConfigProviders.__new__(ConfigProviders)
        handler.get_body_argument = lambda name, default=None: body.get(name, default)
        handler.request = MagicMock()
        handler.request.method = "POST"
        handler.log_configuration_save = MagicMock()
        handler.redirect = MagicMock(return_value="REDIRECT")
        return handler

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_delete_custom_newznab_persists_on_save(self, _notifications, _save_config, _check):
        # Client deleted Jackett from the JS list; KeepMe remains in newznab_string
        handler = self._handler(
            {
                "newznab_string": "KeepMe|https://keep.example/|k1|5030",
                "torrent_rss_string": "RssKeep|https://rss.example/feed||title",
                "provider_order": "keepme:0",
            }
        )
        handler.saveProviders()

        ids = [p.get_id() for p in settings.newznab_provider_list]
        self.assertEqual(ids, ["keepme"])
        self.assertNotIn("jackett", ids)
        self.assertIn("KeepMe|", settings.NEWZNAB_DATA)
        self.assertNotIn("Jackett|", settings.NEWZNAB_DATA)

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_delete_all_custom_newznab_with_empty_string(self, _notifications, _save_config, _check):
        # Empty submitted string must clear customs (previous bug: truthy check skipped deletes)
        handler = self._handler(
            {
                "newznab_string": "",
                "torrent_rss_string": "",
                "provider_order": "",
            }
        )
        handler.saveProviders()

        self.assertEqual(settings.newznab_provider_list, [])
        self.assertEqual(settings.torrent_rss_provider_list, [])
        self.assertEqual(settings.NEWZNAB_DATA, "")

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_missing_newznab_string_leaves_list_unchanged(self, _notifications, _save_config, _check):
        # Section not in the form (NZB search disabled) — do not wipe customs
        before = list(settings.newznab_provider_list)
        handler = self._handler({"provider_order": "keepme:0"})
        handler.saveProviders()
        self.assertEqual(settings.newznab_provider_list, before)

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_provider_order_rejects_malformed_entries(self, _notifications, _save_config, _check):
        settings.newznab_provider_list[0].enabled = True
        handler = self._handler(
            {
                "newznab_string": "KeepMe|https://keep.example/|k1|5030",
                "torrent_rss_string": "RssKeep|https://rss.example/feed||title",
                # valid keepme:0 plus junk: missing flag, bad flag, extra colon, unknown id, empty
                "provider_order": "keepme:0 junk keepme:2 keepme:0:1 notaprovider:1 :1 keepme:",
            }
        )
        handler.saveProviders()
        # Disabled-only POST → persisted PROVIDER_ORDER is enabled-only (empty here)
        self.assertEqual(settings.PROVIDER_ORDER, [])
        self.assertFalse(settings.newznab_provider_list[0].enabled)

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_provider_order_persists_enabled_only(self, _notifications, _save_config, _check):
        handler = self._handler(
            {
                "newznab_string": "KeepMe|https://keep.example/|k1|5030",
                "torrent_rss_string": "RssKeep|https://rss.example/feed||title",
                "provider_order": "keepme:1 rsskeep:0",
            }
        )
        handler.saveProviders()
        self.assertEqual(settings.PROVIDER_ORDER, ["keepme"])
        self.assertTrue(settings.newznab_provider_list[0].enabled)
        self.assertFalse(settings.torrent_rss_provider_list[0].enabled)

    @patch("sickchill.oldbeard.providers.check_enabled_providers")
    @patch("sickchill.start.save_config")
    @patch("sickchill.oldbeard.ui.notifications")
    def test_delete_custom_prunes_providers_section(self, _notifications, _save_config, _check):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(
            cfg,
            "keepme",
            {"type": "newznab", "name": "KeepMe", "url": "https://keep.example/", "key": "k1", "enabled": False},
        )
        write_provider_section(
            cfg,
            "jackett",
            {"type": "newznab", "name": "Jackett", "url": "http://127.0.0.1:9117/", "key": "secret", "enabled": False},
        )
        write_provider_section(
            cfg,
            "rsskeep",
            {"type": "torrentrss", "name": "RssKeep", "url": "https://rss.example/feed", "enabled": False},
        )
        write_provider_section(
            cfg,
            "rssdrop",
            {"type": "torrentrss", "name": "RssDrop", "url": "https://rss.example/drop", "enabled": False},
        )
        settings.CFG = cfg

        handler = self._handler(
            {
                "newznab_string": "KeepMe|https://keep.example/|k1|5030",
                "torrent_rss_string": "RssKeep|https://rss.example/feed||title",
                "provider_order": "keepme:0 rsskeep:0",
            }
        )
        handler.saveProviders()

        self.assertIn("keepme", cfg["PROVIDERS"])
        self.assertIn("rsskeep", cfg["PROVIDERS"])
        self.assertNotIn("jackett", cfg["PROVIDERS"])
        self.assertNotIn("rssdrop", cfg["PROVIDERS"])


if __name__ == "__main__":
    unittest.main()
