"""
Unit tests for TheTVDB API v4 client and indexer adapters (mocked HTTP).
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.show.indexers.tvdb import TVDB, _episode_dict, _SeriesResult, _UpdatesResult
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
            "genres": [{"name": "Drama"}, {"name": "Fantasy"}],
            "companies": [{"name": "HBO", "companyType": {"companyTypeName": "Network"}}],
            "remoteIds": [{"type": 2, "id": "tt0944947"}],
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
        self.assertEqual(series.airsDayOfWeek, "Sunday")
        self.assertEqual(series.airsTime, "21:00")
        self.assertEqual(series.genre, ["Drama", "Fantasy"])
        self.assertIs(series.info("en"), series)


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

        with patch.object(self.client._session, "request", side_effect=[page0, page1]):
            eps = self.client.all_episodes(10, "default")
            self.assertEqual(len(eps), 2)
            self.assertEqual(eps[0]["id"], 1)
            self.assertEqual(eps[1]["id"], 2)


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


if __name__ == "__main__":
    unittest.main()
