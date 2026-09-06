"""Unit tests for the built-in Jackett torrent provider."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill import settings
from sickchill.oldbeard.providers.jackett import Provider, warn_jackett_newznab_overlap
from sickchill.providers.GenericProvider import GenericProvider


class JackettProviderTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            "USE_TORRENTS": settings.USE_TORRENTS,
            "USE_NZBS": settings.USE_NZBS,
            "providerList": settings.providerList,
            "newznab_provider_list": settings.newznab_provider_list,
        }
        self.provider = Provider()
        self.provider.custom_url = "http://127.0.0.1:9117"
        self.provider.api_key = "test-key"
        self.provider.indexer = "all"

    def tearDown(self):
        settings.USE_TORRENTS = self._saved["USE_TORRENTS"]
        settings.USE_NZBS = self._saved["USE_NZBS"]
        settings.providerList = self._saved["providerList"]
        settings.newznab_provider_list = self._saved["newznab_provider_list"]

    def test_provider_type_is_torrent(self):
        self.assertEqual(self.provider.provider_type, GenericProvider.TORRENT)

    def test_is_active_requires_use_torrents_not_nzbs(self):
        self.provider.enabled = True
        settings.USE_TORRENTS = False
        settings.USE_NZBS = True
        self.assertFalse(self.provider.is_active)

        settings.USE_TORRENTS = True
        settings.USE_NZBS = False
        self.assertTrue(self.provider.is_active)

    def test_torznab_url_from_base_and_indexer(self):
        # Jackett README: .../results/torznab/api?apikey=...&t=search
        self.assertEqual(
            self.provider.torznab_url,
            "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/api",
        )
        self.provider.indexer = "thepiratebay"
        self.assertEqual(
            self.provider.torznab_url,
            "http://127.0.0.1:9117/api/v2.0/indexers/thepiratebay/results/torznab/api",
        )

    def test_torznab_url_accepts_full_feed(self):
        full = "http://jackett:9117/api/v2.0/indexers/all/results/torznab/"
        self.provider.custom_url = full
        self.assertEqual(self.provider.torznab_url, "http://jackett:9117/api/v2.0/indexers/all/results/torznab/api")

        already = "http://jackett:9117/api/v2.0/indexers/all/results/torznab/api"
        self.provider.custom_url = already
        self.assertEqual(self.provider.torznab_url, already)

    def test_check_auth_requires_key(self):
        self.provider.api_key = ""
        self.assertFalse(self.provider._check_auth())
        self.provider.api_key = "abc"
        self.assertTrue(self.provider._check_auth())

    @patch("sickchill.oldbeard.providers.jackett.logger")
    def test_warn_overlap_one_warning_per_matching_provider(self, mock_logger):
        jackett = Provider()
        jackett.enabled = True
        settings.providerList = [jackett]
        settings.USE_TORRENTS = True

        fake_nzb = MagicMock()
        fake_nzb.name = "MyJackett"
        fake_nzb.url = "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/"
        settings.newznab_provider_list = [fake_nzb]

        warn_jackett_newznab_overlap()
        self.assertEqual(mock_logger.warning.call_count, 1)

        mock_logger.reset_mock()
        jackett.enabled = False
        warn_jackett_newznab_overlap()
        mock_logger.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
