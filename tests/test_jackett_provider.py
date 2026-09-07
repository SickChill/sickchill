"""Unit tests for the built-in Jackett torrent provider."""

from __future__ import annotations

import unittest
from datetime import date
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
            "CPU_PRESET": settings.CPU_PRESET,
        }
        settings.CPU_PRESET = "NORMAL"
        self.provider = Provider()
        self.provider.custom_url = "http://127.0.0.1:9117"
        self.provider.api_key = "test-key"
        self.provider.indexer = "all"

    def tearDown(self):
        settings.USE_TORRENTS = self._saved["USE_TORRENTS"]
        settings.USE_NZBS = self._saved["USE_NZBS"]
        settings.providerList = self._saved["providerList"]
        settings.newznab_provider_list = self._saved["newznab_provider_list"]
        settings.CPU_PRESET = self._saved["CPU_PRESET"]

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

    def test_torznab_url_strips_apikey_query_from_feed(self):
        """Pasted Jackett copy-feed URLs often include ?apikey=… — strip before path rules."""
        with_key = "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/api?apikey=SECRET&t=search"
        self.provider.custom_url = with_key
        self.assertEqual(
            self.provider.torznab_url,
            "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/api",
        )

        feed_root = "http://jackett:9117/api/v2.0/indexers/all/results/torznab/?apikey=SECRET"
        self.provider.custom_url = feed_root
        self.assertEqual(
            self.provider.torznab_url,
            "http://jackett:9117/api/v2.0/indexers/all/results/torznab/api",
        )

    def test_check_auth_requires_key(self):
        self.provider.api_key = ""
        self.assertFalse(self.provider._check_auth())
        self.provider.api_key = "abc"
        self.assertTrue(self.provider._check_auth())

    def test_check_auth_rejects_non_loopback_http_with_apikey(self):
        self.provider.custom_url = "http://jackett.example.com:9117"
        self.assertFalse(self.provider._check_auth())

        self.provider.custom_url = "https://jackett.example.com:9117"
        self.assertTrue(self.provider._check_auth())

        # Loopback HTTP still allowed (bare "localhost" fails validators.url)
        self.provider.custom_url = "http://127.0.0.1:9117"
        self.assertTrue(self.provider._check_auth())
        self.provider.custom_url = "http://[::1]:9117"
        self.assertTrue(self.provider._check_auth())

        # Private / LAN / hostname HTTP requires HTTPS (apikey in query string)
        self.provider.custom_url = "http://192.168.1.10:9117"
        self.assertFalse(self.provider._check_auth())
        self.provider.custom_url = "https://192.168.1.10:9117"
        self.assertTrue(self.provider._check_auth())
        self.provider.custom_url = "http://jackett.local:9117"
        self.assertFalse(self.provider._check_auth())
        self.provider.custom_url = "https://jackett.local:9117"
        self.assertTrue(self.provider._check_auth())

    def test_url_allows_apikey_transport_helpers(self):
        allow = Provider._url_allows_apikey_transport
        self.assertTrue(allow("https://remote.example/jackett"))
        self.assertTrue(allow("http://127.0.0.1:9117"))
        self.assertTrue(allow("http://localhost:9117"))
        self.assertTrue(allow("http://[::1]:9117"))
        self.assertTrue(allow("https://192.168.1.10:9117"))
        self.assertTrue(allow("https://jackett.local:9117"))
        self.assertFalse(allow("http://10.0.0.5:9117"))
        self.assertFalse(allow("http://192.168.1.10:9117"))
        self.assertFalse(allow("http://jackett:9117"))
        self.assertFalse(allow("http://nas.local:9117"))
        self.assertFalse(allow("http://remote.example:9117"))
        self.assertFalse(allow("ftp://127.0.0.1:9117"))

    @patch("sickchill.oldbeard.providers.jackett.time.sleep", return_value=None)
    @patch.object(Provider, "get_url")
    def test_structured_airdate_search_preserves_q(self, mock_get_url, _sleep):
        """Air-date/sports structured search must send q=airdate, not the generic search string."""
        mock_get_url.return_value = "<rss><channel></channel></rss>"

        self.provider.indexer = "thepiratebay"
        self.provider.use_tv_search = True
        self.provider.cap_tv_search = "q,season,ep"
        self.provider._caps = True

        show = MagicMock()
        show.air_by_date = True
        show.sports = False
        show.is_anime = False
        show.indexerid = 12345
        self.provider.show = show

        episode = MagicMock()
        episode.airdate = date(2024, 6, 15)
        self.provider.current_episode_object = episode

        self.provider.search({"Episode": ["Show.Name.S01E01"]})

        mock_get_url.assert_called()
        _args, kwargs = mock_get_url.call_args
        params = kwargs.get("params") or (_args[1] if len(_args) > 1 else None)
        # get_url(url, params=..., returns=...)
        if params is None:
            params = mock_get_url.call_args.kwargs["params"]
        self.assertEqual(params["q"], "2024-06-15")
        self.assertNotEqual(params["q"], "Show.Name.S01E01")

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
