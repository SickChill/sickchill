"""Custom Newznab/TorrentRSS rename vs built-in provider id collisions."""

from __future__ import annotations

import json
import unittest

from sickchill import settings
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.views.config.providers import ConfigProviders


class _Builtin:
    def __init__(self, name: str):
        self.name = name

    def get_id(self, suffix=""):
        return GenericProvider.make_id(self.name) + str(suffix)


class CanAddProviderRenameTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            "newznab_provider_list": settings.newznab_provider_list,
            "torrent_rss_provider_list": settings.torrent_rss_provider_list,
            "providerList": settings.providerList,
        }
        settings.providerList = [_Builtin("Jackett-SC"), _Builtin("TorrentLeech")]
        settings.newznab_provider_list = [
            NewznabProvider("Jackett-SC", "http://127.0.0.1:9117/", key="secret", categories="5000"),
            NewznabProvider("KeepMe", "https://keep.example/", key="k1", categories="5030"),
        ]
        settings.torrent_rss_provider_list = [
            TorrentRssProvider("RssKeep", "https://rss.example/feed", "", "title"),
        ]

    def tearDown(self):
        settings.newznab_provider_list = self._saved["newznab_provider_list"]
        settings.torrent_rss_provider_list = self._saved["torrent_rss_provider_list"]
        settings.providerList = self._saved["providerList"]

    def test_make_id_jackett_sc_collides_with_builtin(self):
        self.assertEqual(GenericProvider.make_id("Jackett-SC"), "jackett_sc")
        self.assertEqual(GenericProvider.make_id("Jackett SC"), "jackett_sc")

    def test_can_add_rejects_builtin_id(self):
        result = json.loads(ConfigProviders.canAddNewznabProvider("TorrentLeech"))
        self.assertIn("error", result)
        self.assertIn("torrentleech", result["error"])

    def test_can_add_rejects_existing_custom(self):
        result = json.loads(ConfigProviders.canAddNewznabProvider("KeepMe"))
        self.assertIn("error", result)

    def test_rename_exclude_allows_same_id(self):
        # Renaming Jackett-SC → Jackett SC still normalizes to jackett_sc; exclude current id
        result = json.loads(ConfigProviders.canAddNewznabProvider("Jackett SC", exclude_id="jackett_sc"))
        self.assertEqual(result.get("success"), "jackett_sc")

    def test_rename_to_free_name_succeeds(self):
        result = json.loads(ConfigProviders.canAddNewznabProvider("My Jackett", exclude_id="jackett_sc"))
        self.assertEqual(result.get("success"), "my_jackett")

    def test_rename_onto_builtin_still_rejected(self):
        # Even with exclude of a different custom, cannot take torrentleech
        result = json.loads(ConfigProviders.canAddNewznabProvider("TorrentLeech", exclude_id="jackett_sc"))
        self.assertIn("error", result)

    def test_torrent_rss_rejects_builtin(self):
        result = json.loads(ConfigProviders.canAddTorrentRssProvider("Jackett-SC", "https://rss.example/x", "", "title"))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
