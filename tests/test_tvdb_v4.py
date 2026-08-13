"""
Unit tests for TheTVDB API v4 client and indexer adapters (mocked HTTP).
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.show.indexers.tvdb import (
    TVDB,
    _apply_series_translation,
    _episode_dict,
    _SeriesResult,
    _tvdb_language_candidates,
    _UpdatesResult,
)
from sickchill.show.indexers.tvdb_v4_client import TVDBv4Client, TVDBv4Error, TVDBv4NotModified


class EpisodeDictMappingTests(unittest.TestCase):
    def test_episode_dict_maps_v4_fields(self):
        raw = {
            "id": 99,
            "seasonNumber": 2,
            "number": 5,
            "name": "Pilot Title",
            "absoluteNumber": 15,
            "overview": "Plot",
            "aired": "2024-01-02",
            "image": "https://artworks.thetvdb.com/banners/ep.jpg",
            "lastUpdated": 1700000000,
        }
        mapped = _episode_dict(raw)
        self.assertEqual(mapped["id"], 99)
        self.assertEqual(mapped["airedSeason"], 2)
        self.assertEqual(mapped["airedEpisodeNumber"], 5)
        self.assertEqual(mapped["episodeName"], "Pilot Title")
        self.assertEqual(mapped["absoluteNumber"], 15)
        self.assertEqual(mapped["overview"], "Plot")
        self.assertEqual(mapped["firstAired"], "2024-01-02")
        self.assertEqual(mapped["filename"], "https://artworks.thetvdb.com/banners/ep.jpg")
        self.assertEqual(mapped["lastUpdated"], 1700000000)


class SeriesResultMappingTests(unittest.TestCase):
    def test_series_result_basic_fields(self):
        raw = {
            "id": 121361,
            "name": "Game of Thrones",
            "overview": "Winter is coming",
            "status": {"name": "Ended"},
            "firstAired": "2011-04-17",
            "averageRuntime": 55,
            "score": 9.1,
            "genres": [{"name": "Drama"}, {"name": "Fantasy"}],
            "companies": [{"name": "HBO", "companyType": {"companyTypeName": "Network"}}],
            "remoteIds": [
                {"type": 2, "id": "tt0944947"},
                {"sourceName": "zap2it", "id": "EP123"},
            ],
            "contentRatings": [{"name": "TV-MA", "country": "usa"}],
            "airsDays": {"sunday": True, "monday": False},
            "airsTime": "21:00",
            "artworks": [{"type": 2, "image": "https://example.com/poster.jpg", "score": 10}],
            "lastUpdated": 1600000000,
        }
        series = _SeriesResult(raw, language="en")
        self.assertEqual(series.id, 121361)
        self.assertEqual(series.seriesName, "Game of Thrones")
        self.assertEqual(series.status, "Ended")
        self.assertEqual(series.network, "HBO")
        self.assertEqual(series.imdbId, "tt0944947")
        self.assertEqual(series.zap2itId, "EP123")
        self.assertEqual(series.siteRating, 9.1)
        self.assertEqual(series.rating, "TV-MA")
        self.assertEqual(series.contentRating, "TV-MA")
        self.assertEqual(series.airsDayOfWeek, "Sunday")
        self.assertEqual(series.airsTime, "21:00")
        self.assertEqual(series.genre, ["Drama", "Fantasy"])
        self.assertIs(series.info("en"), series)
        # __getitem__ string-key behaviour unchanged
        self.assertEqual(series["seriesName"], "Game of Thrones")

    def test_language_candidates_include_tvdb_codes(self):
        self.assertIn("eng", _tvdb_language_candidates("en"))
        self.assertIn("zho", _tvdb_language_candidates("zh"))
        self.assertIn("zho", _tvdb_language_candidates("zh_CN"))

    def test_apply_series_translation_overlays_name(self):
        raw = {"id": 1, "name": "吞噬星空", "overview": "中文简介"}
        applied = _apply_series_translation(raw, {"name": "Tunshi Xingkong", "overview": "English overview"})
        self.assertEqual(applied["name"], "Tunshi Xingkong")
        self.assertEqual(applied["overview"], "English overview")
        # original dict not mutated
        self.assertEqual(raw["name"], "吞噬星空")


class SeriesLanguageTests(unittest.TestCase):
    def _mock_client_for(self, tvdb: TVDB) -> MagicMock:
        """Attach a MagicMock client that matches api_key so client property does not replace it."""
        from sickchill import settings

        client = MagicMock()
        client.apikey = tvdb.api_key or settings.TVDB_V4_APIKEY
        client.pin = getattr(settings, "TVDB_V4_PIN", None) or ""
        client.timeout = getattr(settings, "INDEXER_TIMEOUT", None) or 20
        tvdb._client = client
        return client

    def test_english_translation_applied_for_chinese_primary_title(self):
        """Regression: show.lang=en must not keep primary Chinese title when eng translation exists."""
        tvdb = TVDB()
        client = self._mock_client_for(tvdb)
        client.series_extended.return_value = {
            "id": 392226,
            "name": "吞噬星空",
            "overview": "中文",
            "status": {"name": "Continuing"},
            "genres": [],
            "companies": [],
            "remoteIds": [],
            "artworks": [],
        }
        client.series_translation.side_effect = lambda sid, code: {"name": "Tunshi Xingkong", "overview": "In a future where..."} if code == "eng" else None

        result = tvdb.series(392226, language="en")
        self.assertIsNotNone(result)
        self.assertNotIsInstance(result, list)
        self.assertEqual(result.seriesName, "Tunshi Xingkong")
        self.assertEqual(result.overview, "In a future where...")
        client.series_translation.assert_any_call(392226, "eng")

    def test_chinese_translation_when_lang_zh(self):
        tvdb = TVDB()
        client = self._mock_client_for(tvdb)
        client.series_extended.return_value = {
            "id": 392226,
            "name": "Swallowed Star",
            "overview": "English",
            "status": {"name": "Continuing"},
            "genres": [],
            "companies": [],
            "remoteIds": [],
            "artworks": [],
        }
        client.series_translation.side_effect = lambda sid, code: {"name": "吞噬星空", "overview": "中文简介"} if code in ("zho", "zh") else None

        result = tvdb.series(392226, language="zh")
        self.assertNotIsInstance(result, list)
        self.assertEqual(result.seriesName, "吞噬星空")


class TVDBv4ClientTests(unittest.TestCase):
    def setUp(self):
        self.client = TVDBv4Client("test-key", pin="pin", timeout=5)

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_search_returns_list(self, _headers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"status":"success","data":[{"tvdb_id":"123","name":"Show"}]}'
        mock_response.json.return_value = {"status": "success", "data": [{"tvdb_id": "123", "name": "Show"}]}
        mock_response.headers = {}

        with patch.object(self.client._session, "request", return_value=mock_response) as request:
            result = self.client.search("Show")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "Show")
            request.assert_called()

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_404_returns_none(self, _headers):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = b""
        mock_response.headers = {}

        with patch.object(self.client._session, "request", return_value=mock_response):
            self.assertIsNone(self.client.series_extended(999999))

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_304_raises_not_modified(self, _headers):
        mock_response = MagicMock()
        mock_response.status_code = 304
        mock_response.content = b""
        mock_response.headers = {}

        with patch.object(self.client._session, "request", return_value=mock_response):
            with self.assertRaises(TVDBv4NotModified):
                self.client.series_extended(1, if_modified_since="Wed, 01 Jan 2020 00:00:00 GMT")

    def test_401_retries_once(self):
        unauthorized = MagicMock()
        unauthorized.status_code = 401
        unauthorized.content = b'{"status":"failure"}'
        unauthorized.json.return_value = {"status": "failure"}
        unauthorized.headers = {}

        ok = MagicMock()
        ok.status_code = 200
        ok.content = b'{"status":"success","data":{"id":1}}'
        ok.json.return_value = {"status": "success", "data": {"id": 1}}
        ok.headers = {}

        # Seed a token so first request does not login; 401 clears it and second _headers logs in again.
        self.client._token = "stale"
        self.client._token_time = 10**12

        with patch.object(self.client._session, "request", side_effect=[unauthorized, ok]) as request:
            with patch.object(self.client, "_login", wraps=self.client._login) as login:
                # Prevent real network login; set a fresh token when called
                def fake_login():
                    self.client._token = "fresh"
                    self.client._token_time = 10**12

                login.side_effect = fake_login
                result = self.client.series(1)
                self.assertEqual(result["id"], 1)
                self.assertEqual(request.call_count, 2)
                login.assert_called()

    def test_login_requires_apikey(self):
        client = TVDBv4Client("")
        with self.assertRaises(TVDBv4Error):
            client._login()

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_all_episodes_paginates(self, _headers):
        page0 = MagicMock()
        page0.status_code = 200
        page0.headers = {}
        page0.content = b"{}"
        page0.json.return_value = {
            "status": "success",
            "data": {
                "episodes": [{"id": 1, "number": 1, "seasonNumber": 1, "name": "One"}],
                "links": {"next": 1},
            },
        }

        page1 = MagicMock()
        page1.status_code = 200
        page1.headers = {}
        page1.content = b"{}"
        page1.json.return_value = {
            "status": "success",
            "data": {
                "episodes": [{"id": 2, "number": 2, "seasonNumber": 1, "name": "Two"}],
                "links": {},
            },
        }

        with patch.object(self.client._session, "request", side_effect=[page0, page1]) as request:
            eps = self.client.all_episodes(10, "default")
            self.assertEqual(len(eps), 2)
            self.assertEqual(eps[0]["id"], 1)
            self.assertEqual(eps[1]["id"], 2)
            self.assertEqual(request.call_count, 2)
            # Second request must use page from page0 links.next (value 1)
            second_params = request.call_args_list[1].kwargs.get("params") or {}
            self.assertEqual(int(second_params.get("page")), int(page0.json.return_value["data"]["links"]["next"]))


class UpdatesCompatTests(unittest.TestCase):
    def test_updates_collects_series_ids(self):
        client = MagicMock()
        client.all_updates_since.return_value = [
            {"recordType": "series", "recordId": 11},
            {"entityType": "series", "id": 22},
            {"recordType": "episode", "seriesId": 33},
            {"recordType": "series", "recordId": 11},  # dupe
        ]
        updates = _UpdatesResult(client, from_time=1000)
        series = updates.series()
        ids = sorted(item["id"] for item in series)
        self.assertEqual(ids, [11, 22, 33])


class TVDBSearchMappingTests(unittest.TestCase):
    def test_map_search_results_strips_series_prefix(self):
        raw = [
            {"tvdb_id": "series-78804", "name": "Doctor Who", "first_air_time": "2005-03-26", "score": 100},
            {"tvdb_id": "series-78804", "name": "Doctor Who Dup"},  # dupe id
        ]
        mapped = TVDB._map_search_results(raw)
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["id"], 78804)
        self.assertEqual(mapped[0]["seriesName"], "Doctor Who")
        self.assertEqual(mapped[0]["firstAired"], "2005-03-26")

    def test_complete_image_url_passthrough_and_relative(self):
        self.assertEqual(TVDB.complete_image_url("https://cdn.example/a.jpg"), "https://cdn.example/a.jpg")
        self.assertTrue(TVDB.complete_image_url("posters/foo.jpg").startswith("https://artworks.thetvdb.com/"))
        self.assertEqual(TVDB.complete_image_url(""), "")

    def test_favorites_noop(self):
        tvdb = TVDB()
        self.assertEqual(tvdb.get_favorites(), [])
        self.assertFalse(TVDB.test_user_key("u", "k"))

    def test_api_key_uses_settings_only(self):
        from sickchill import settings

        previous = settings.TVDB_V4_APIKEY
        try:
            settings.TVDB_V4_APIKEY = "unit-test-key"
            self.assertEqual(TVDB().api_key, "unit-test-key")
            settings.TVDB_V4_APIKEY = previous
            self.assertEqual(TVDB().api_key, settings.TVDB_V4_APIKEY)
            self.assertTrue(len(TVDB().api_key) > 10)
        finally:
            settings.TVDB_V4_APIKEY = previous

    def test_tvdb_v4_apikey_default_is_not_raw_uuid_in_source(self):
        """Guard: settings module should not contain the decoded key as a raw string literal."""
        import inspect
        from pathlib import Path

        from sickchill import settings as settings_mod

        source = Path(inspect.getfile(settings_mod)).read_text(encoding="utf-8")
        self.assertNotIn(settings_mod.TVDB_V4_APIKEY, source)


if __name__ == "__main__":
    unittest.main()
