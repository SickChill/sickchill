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
            "torrent_rss_provider_list": settings.torrent_rss_provider_list,
            "PROVIDER_ORDER": settings.PROVIDER_ORDER,
            "CPU_PRESET": settings.CPU_PRESET,
        }
        settings.CPU_PRESET = "NORMAL"
        settings.PROVIDER_ORDER = []
        settings.torrent_rss_provider_list = []
        self.provider = Provider()
        self.provider.custom_url = "http://127.0.0.1:9117"
        self.provider.api_key = "test-key"
        self.provider.indexer = "all"

    def tearDown(self):
        settings.USE_TORRENTS = self._saved["USE_TORRENTS"]
        settings.USE_NZBS = self._saved["USE_NZBS"]
        settings.providerList = self._saved["providerList"]
        settings.newznab_provider_list = self._saved["newznab_provider_list"]
        settings.torrent_rss_provider_list = self._saved["torrent_rss_provider_list"]
        settings.PROVIDER_ORDER = self._saved["PROVIDER_ORDER"]
        settings.CPU_PRESET = self._saved["CPU_PRESET"]

    def test_provider_type_is_torrent(self):
        self.assertEqual(self.provider.provider_type, GenericProvider.TORRENT)

    def test_default_site_url_and_api_key(self):
        fresh = Provider()
        self.assertEqual(fresh.custom_url, "http://127.0.0.1:9117")
        self.assertEqual(fresh.api_key, "9dxv8e0lv3z9os1lzqt97klpucon60z8")

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

    def test_check_auth_http_local_vs_public(self):
        # Public hostname over HTTP still rejected (apikey in query string)
        self.provider.custom_url = "http://jackett.example.com:9117"
        self.assertFalse(self.provider._check_auth())
        self.provider.custom_url = "https://jackett.example.com:9117"
        self.assertTrue(self.provider._check_auth())

        # Loopback HTTP allowed (bare "localhost" fails validators.url)
        self.provider.custom_url = "http://127.0.0.1:9117"
        self.assertTrue(self.provider._check_auth())
        self.provider.custom_url = "http://[::1]:9117"
        self.assertTrue(self.provider._check_auth())

        # Docker bridge → host LAN IP (Jackett published port) over HTTP
        self.provider.custom_url = "http://192.168.1.10:9117"
        self.assertTrue(self.provider._check_auth())
        self.provider.custom_url = "https://192.168.1.10:9117"
        self.assertTrue(self.provider._check_auth())

        # Same Compose network by service name / .local over HTTP
        self.provider.custom_url = "http://jackett:9117"
        self.assertTrue(self.provider._check_auth())
        self.provider.custom_url = "http://jackett.local:9117"
        self.assertTrue(self.provider._check_auth())
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
        # Private / Docker-local HTTP (bridge → host IP, Compose service name)
        self.assertTrue(allow("http://10.0.0.5:9117"))
        self.assertTrue(allow("http://192.168.1.10:9117"))
        self.assertTrue(allow("http://172.16.5.1:9117"))
        self.assertTrue(allow("http://jackett:9117"))
        self.assertTrue(allow("http://host.docker.internal:9117"))
        self.assertTrue(allow("http://nas.local:9117"))
        # Public cleartext still blocked
        self.assertFalse(allow("http://remote.example:9117"))
        self.assertFalse(allow("http://8.8.8.8:9117"))
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
        fake_nzb.get_id.return_value = "myjackett"
        fake_nzb.url = "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/"
        settings.newznab_provider_list = [fake_nzb]

        warn_jackett_newznab_overlap()
        self.assertEqual(mock_logger.warning.call_count, 1)

        mock_logger.reset_mock()
        jackett.enabled = False
        warn_jackett_newznab_overlap()
        mock_logger.warning.assert_not_called()

    def test_provider_display_name_and_id(self):
        self.assertEqual(self.provider.name, "Jackett-SC")
        self.assertEqual(self.provider.get_id(), "jackett_sc")

    @patch("sickchill.oldbeard.providers.jackett.logger")
    def test_warn_overlap_name_collision_even_if_builtin_disabled(self, mock_logger):
        jackett = Provider()
        jackett.enabled = False
        settings.providerList = [jackett]

        # Custom named exactly like the built-in still conflicts on id
        fake_nzb = MagicMock()
        fake_nzb.name = "Jackett-SC"
        fake_nzb.get_id.return_value = "jackett_sc"
        fake_nzb.url = "http://127.0.0.1:9117/"
        settings.newznab_provider_list = [fake_nzb]

        warn_jackett_newznab_overlap()
        self.assertEqual(mock_logger.warning.call_count, 1)
        self.assertIn("conflicts with built-in", mock_logger.warning.call_args[0][0])

    def test_custom_newznab_named_jackett_coexists_with_builtin(self):
        """Custom Newznab 'Jackett' (id jackett) must not hide built-in Jackett-SC."""
        from sickchill.oldbeard.providers import sorted_provider_list
        from sickchill.oldbeard.providers.newznab import NewznabProvider

        builtin = Provider()
        settings.providerList = [builtin]
        custom = NewznabProvider("Jackett", "http://127.0.0.1:9117/api/v2.0/indexers/all/results/torznab/")
        settings.newznab_provider_list = [custom]
        settings.USE_TORRENTS = True
        settings.USE_NZBS = True

        providers = sorted_provider_list(only_enabled=True)
        by_id = {p.get_id(): p for p in providers}
        self.assertIn("jackett_sc", by_id)
        self.assertIn("jackett", by_id)
        self.assertEqual(by_id["jackett_sc"].provider_type, GenericProvider.TORRENT)
        self.assertEqual(by_id["jackett"].provider_type, GenericProvider.NZB)
        self.assertIs(by_id["jackett_sc"], builtin)

        # NZB-only: custom Jackett remains; built-in Jackett-SC is filtered out
        settings.USE_TORRENTS = False
        settings.USE_NZBS = True
        providers = sorted_provider_list(only_enabled=True)
        ids = {p.get_id() for p in providers}
        self.assertIn("jackett", ids)
        self.assertNotIn("jackett_sc", ids)

        # Torrents-only: built-in only
        settings.USE_TORRENTS = True
        settings.USE_NZBS = False
        providers = sorted_provider_list(only_enabled=True)
        ids = {p.get_id() for p in providers}
        self.assertIn("jackett_sc", ids)
        self.assertNotIn("jackett", ids)

    @patch.object(Provider, "get_url")
    def test_get_jackett_categories_parses_tv_caps(self, mock_get_url):
        mock_get_url.return_value = """<?xml version="1.0"?>
        <caps>
          <searching>
            <search available="yes"/>
            <tv-search available="yes" supportedParams="q,season,ep"/>
          </searching>
          <categories>
            <category id="2000" name="Movies"/>
            <category id="5000" name="TV">
              <subcat id="5030" name="HD"/>
              <subcat id="5040" name="SD"/>
            </category>
            <category id="5070" name="Anime"/>
          </categories>
        </caps>
        """
        ok, cats, err = self.provider.get_jackett_categories()
        self.assertTrue(ok, err)
        ids = [c["id"] for c in cats]
        self.assertIn("5000", ids)
        self.assertIn("5030", ids)
        self.assertIn("5040", ids)
        # Torznab anime is TV-range 5070
        self.assertIn("5070", ids)
        self.assertNotIn("2000", ids)
        mock_get_url.assert_called()
        self.assertFalse(mock_get_url.call_args.kwargs.get("allow_redirects", True))

    @patch.object(Provider, "get_url")
    def test_get_jackett_categories_empty_tv_fails(self, mock_get_url):
        mock_get_url.return_value = """<?xml version="1.0"?>
        <caps>
          <searching><search available="yes"/></searching>
          <categories>
            <category id="2000" name="Movies"/>
          </categories>
        </caps>
        """
        ok, cats, err = self.provider.get_jackett_categories()
        self.assertFalse(ok)
        self.assertEqual(cats, [])
        self.assertIn("No TV categories", err)


if __name__ == "__main__":
    unittest.main()
