"""
Unit tests for TheTVDB API v4 client and indexer adapters (mocked HTTP).
"""

from __future__ import annotations

import datetime
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


def attach_mock_client(tvdb: TVDB) -> MagicMock:
    """Attach a MagicMock client that matches TVDB.client property re-init checks."""
    from sickchill import settings

    client = MagicMock()
    client.apikey = tvdb.api_key or settings.TVDB_V4_APIKEY
    client.pin = getattr(settings, "TVDB_V4_PIN", None) or ""
    client.timeout = getattr(settings, "INDEXER_TIMEOUT", None) or 20
    tvdb._client = client
    return client


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

    def test_apply_series_translation_noop_same_text(self):
        raw = {"id": 1, "name": "Dutton Ranch", "overview": "A show"}
        applied = _apply_series_translation(raw, {"name": "Dutton Ranch", "overview": "A show"})
        self.assertIs(applied, raw)


class SeriesLanguageTests(unittest.TestCase):
    def test_english_translation_applied_for_chinese_primary_title(self):
        """Regression: show.lang=en must not keep primary Chinese title when eng translation exists."""
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
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
        client = attach_mock_client(tvdb)
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

    def test_series_cache_reuses_extended_and_translation(self):
        """Repeated series() / artwork calls must not re-hit V4 within TTL."""
        from sickchill.show.indexers.tvdb_v4_client import (
            ARTWORK_TYPE_BACKGROUND,
            ARTWORK_TYPE_BANNER,
            ARTWORK_TYPE_POSTER,
        )

        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.series_extended.return_value = {
            "id": 463308,
            "name": "Dutton Ranch",
            "overview": "About ranching",
            "status": {"name": "Continuing"},
            "genres": [],
            "companies": [],
            "remoteIds": [],
            "artworks": [
                {"type": ARTWORK_TYPE_POSTER, "image": "https://example.com/p.jpg", "score": 10},
                {"type": ARTWORK_TYPE_BANNER, "image": "https://example.com/b.jpg", "score": 10},
                {"type": ARTWORK_TYPE_BACKGROUND, "image": "https://example.com/f.jpg", "score": 10},
            ],
            "seasonTypes": [{"type": "default", "name": "Aired Order"}],
            "seasons": [],
        }
        client.series_translation.return_value = {"name": "Dutton Ranch", "overview": "About ranching"}

        show = MagicMock()
        show.indexerid = 463308
        show.lang = "en"

        first = tvdb.series(show)
        second = tvdb.series(show)
        self.assertEqual(first.seriesName, "Dutton Ranch")
        self.assertEqual(second.seriesName, "Dutton Ranch")
        self.assertEqual(client.series_extended.call_count, 1)
        self.assertEqual(client.series_translation.call_count, 1)

        # Artwork types share the same cached series payload
        self.assertTrue(tvdb.series_poster_url(show))
        self.assertTrue(tvdb.series_banner_url(show))
        self.assertTrue(tvdb.series_fanart_url(show))
        self.assertEqual(client.series_extended.call_count, 1)
        self.assertEqual(client.series_translation.call_count, 1)

        # Season types reuse extended cache (no second HTTP)
        types = tvdb._fetch_series_season_types(463308)
        self.assertEqual(types[0]["slug"], "default")
        self.assertEqual(client.series_extended.call_count, 1)

        tvdb.clear_episode_cache(463308)
        tvdb.series(show)
        self.assertEqual(client.series_extended.call_count, 2)


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
                first_headers = request.call_args_list[0].kwargs.get("headers") or {}
                second_headers = request.call_args_list[1].kwargs.get("headers") or {}
                self.assertEqual(first_headers.get("Authorization"), "Bearer stale")
                self.assertEqual(second_headers.get("Authorization"), "Bearer fresh")

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
            },
            "links": {"next": 1},
        }

        page1 = MagicMock()
        page1.status_code = 200
        page1.headers = {}
        page1.content = b"{}"
        page1.json.return_value = {
            "status": "success",
            "data": {
                "episodes": [{"id": 2, "number": 2, "seasonNumber": 1, "name": "Two"}],
            },
            "links": {},
        }

        with patch.object(self.client._session, "request", side_effect=[page0, page1]) as request:
            eps = self.client.all_episodes(10, "default")
            self.assertEqual(len(eps), 2)
            self.assertEqual(eps[0]["id"], 1)
            self.assertEqual(eps[1]["id"], 2)
            self.assertEqual(request.call_count, 2)
            # Second request must use page from page0 links.next (value 1)
            second_params = request.call_args_list[1].kwargs.get("params") or {}
            self.assertEqual(int(second_params.get("page")), 1)

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_429_retries_then_succeeds(self, _headers):
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.content = b"{}"
        rate_limited.headers = {"Retry-After": "1"}
        rate_limited.json.return_value = {"status": "failure", "message": "rate limit"}

        ok = MagicMock()
        ok.status_code = 200
        ok.content = b"{}"
        ok.headers = {}
        ok.json.return_value = {"status": "success", "data": {"id": 7}}

        with patch.object(self.client._session, "request", side_effect=[rate_limited, ok]) as request:
            with patch("sickchill.show.indexers.tvdb_v4_client.time.sleep") as sleep:
                result = self.client.series(7)
                self.assertEqual(result["id"], 7)
                self.assertEqual(request.call_count, 2)
                sleep.assert_called_with(1.0)

    def test_retry_after_http_date(self):
        from datetime import datetime, timedelta, timezone
        from email.utils import format_datetime

        future = datetime.now(timezone.utc) + timedelta(seconds=3)
        response = MagicMock()
        response.headers = {"Retry-After": format_datetime(future, usegmt=True)}
        delay = TVDBv4Client._retry_delay_seconds(response, attempt=0)
        # Should be ~3s (allow small timing skew); clamped >= 0
        self.assertGreaterEqual(delay, 0.0)
        self.assertLessEqual(delay, 4.0)
        self.assertGreaterEqual(delay, 1.5)

    def test_retry_after_past_http_date_clamps_to_zero(self):
        from datetime import datetime, timedelta, timezone
        from email.utils import format_datetime

        past = datetime.now(timezone.utc) - timedelta(seconds=30)
        response = MagicMock()
        response.headers = {"Retry-After": format_datetime(past, usegmt=True)}
        delay = TVDBv4Client._retry_delay_seconds(response, attempt=0)
        self.assertEqual(delay, 0.0)

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_all_updates_since_follows_links_next(self, _headers):
        page0 = MagicMock()
        page0.status_code = 200
        page0.headers = {}
        page0.content = b"{}"
        page0.json.return_value = {
            "status": "success",
            "data": [{"id": 1, "recordType": "series"}],
            "links": {"next": 1},
        }
        page1 = MagicMock()
        page1.status_code = 200
        page1.headers = {}
        page1.content = b"{}"
        page1.json.return_value = {
            "status": "success",
            "data": [{"id": 2, "recordType": "series"}],
            "links": {},
        }
        with patch.object(self.client._session, "request", side_effect=[page0, page1]) as request:
            updates = self.client.all_updates_since(1000)
            self.assertEqual([u["id"] for u in updates], [1, 2])
            self.assertEqual(request.call_count, 2)
            second_params = request.call_args_list[1].kwargs.get("params") or {}
            self.assertEqual(int(second_params.get("page")), 1)

    @patch.object(TVDBv4Client, "_headers", return_value={"Authorization": "Bearer t"})
    def test_updates_since_links_are_per_response_not_shared(self, _headers):
        """Concurrent interleaved /updates calls must not share pagination links."""
        import threading

        # Response A page0 → next 10; Response B page0 → next 99
        def make_resp(data_id, next_page):
            r = MagicMock()
            r.status_code = 200
            r.headers = {}
            r.content = b"{}"
            r.json.return_value = {
                "status": "success",
                "data": [{"id": data_id, "recordType": "series"}],
                "links": {"next": next_page} if next_page is not None else {},
            }
            return r

        barrier = threading.Barrier(2)
        results = {}

        # Controlled order: both first pages, then follow-ups if any
        responses = {
            ("series", 0): make_resp(1, 10),
            ("episodes", 0): make_resp(2, 99),
        }

        def request_side_effect(method, url, headers=None, params=None, timeout=None):
            params = params or {}
            entity = params.get("type", "series")
            page = int(params.get("page") or 0)
            key = (entity, page)
            if page == 0:
                barrier.wait(timeout=2)
            if key in responses:
                return responses[key]
            # follow-up pages: no further next
            return make_resp(100 + page, None)

        with patch.object(self.client._session, "request", side_effect=request_side_effect):

            def worker(entity_type, out_key):
                batch, links = self.client.updates_since(1000, entity_type=entity_type, page=0)
                results[out_key] = (batch, links)

            t1 = threading.Thread(target=worker, args=("series", "a"))
            t2 = threading.Thread(target=worker, args=("episodes", "b"))
            t1.start()
            t2.start()
            t1.join(timeout=5)
            t2.join(timeout=5)

        self.assertIn("a", results)
        self.assertIn("b", results)
        batch_a, links_a = results["a"]
        batch_b, links_b = results["b"]
        self.assertEqual(batch_a[0]["id"], 1)
        self.assertEqual(batch_b[0]["id"], 2)
        self.assertEqual(links_a.get("next"), 10)
        self.assertEqual(links_b.get("next"), 99)
        # No shared client field for links
        self.assertFalse(hasattr(self.client, "_last_links") and self.client._last_links not in (None, {}))


class ImageApiReturnTypeTests(unittest.TestCase):
    def test_call_images_api_failure_respects_multiple(self):
        tvdb = TVDB()
        show = MagicMock()
        with patch.object(tvdb, "series", side_effect=RuntimeError("boom")):
            self.assertEqual(tvdb.series_poster_url(show, multiple=False), "")
            self.assertEqual(tvdb.series_poster_url(show, multiple=True), [])

    def test_episode_image_url_failure_returns_empty_string(self):
        tvdb = TVDB()
        with patch.object(tvdb, "episode", side_effect=RuntimeError("boom")):
            self.assertEqual(tvdb.episode_image_url(MagicMock()), "")


class UpdatesCompatTests(unittest.TestCase):
    def test_updates_collects_series_ids(self):
        client = MagicMock()

        def all_updates_since(since, entity_type="series", max_pages=50):
            if entity_type == "series":
                return [
                    {"recordType": "series", "recordId": 11},
                    {"entityType": "series", "id": 22},
                    {"recordType": "series", "recordId": 11},  # dupe
                ]
            if entity_type == "episodes":
                return [{"recordType": "episode", "seriesId": 33, "id": 999}]
            return []

        client.all_updates_since.side_effect = all_updates_since
        updates = _UpdatesResult(client, from_time=1000)
        series = updates.series()
        ids = sorted(item["id"] for item in series)
        self.assertEqual(ids, [11, 22, 33])


class EpisodeCacheTests(unittest.TestCase):
    def test_episodes_cache_avoids_second_http(self):
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.all_episodes.return_value = [
            {"id": 1, "seasonNumber": 1, "number": 1, "name": "One", "lastUpdated": 100},
            {"id": 2, "seasonNumber": 1, "number": 2, "name": "Two", "lastUpdated": 200},
        ]
        show = MagicMock()
        show.indexerid = 55
        show.dvdorder = False
        show.lang = "en"

        first = tvdb.episodes(show)
        second = tvdb.episodes(show, season=1)
        self.assertEqual(len(first), 2)
        self.assertEqual(len(second), 2)
        client.all_episodes.assert_called_once()
        # Metadata language en → TVDB eng on translated episode endpoint
        self.assertEqual(client.all_episodes.call_args.kwargs.get("language") or client.all_episodes.call_args[1].get("language"), "eng")

        ep = tvdb.episode(show, 1, 2)
        self.assertEqual(ep["episodeName"], "Two")
        client.all_episodes.assert_called_once()

    def test_clear_episode_cache_forces_refetch(self):
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.all_episodes.return_value = [
            {"id": 1, "seasonNumber": 1, "number": 1, "name": "One", "lastUpdated": 100},
        ]
        show = MagicMock()
        show.indexerid = 77
        show.dvdorder = False
        show.lang = "en"
        tvdb.episodes(show)
        tvdb.clear_episode_cache(77)
        tvdb.episodes(show)
        self.assertEqual(client.all_episodes.call_count, 2)

    def test_episode_cache_ttl_forces_refetch(self):
        """Expired TTL entries are dropped so subsequent loads refresh without clear_episode_cache."""
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.all_episodes.return_value = [
            {"id": 1, "seasonNumber": 1, "number": 1, "name": "One", "lastUpdated": 100},
        ]
        show = MagicMock()
        show.indexerid = 88
        show.dvdorder = False
        show.lang = "en"
        tvdb._episode_cache_ttl = -1.0  # always expired vs monotonic age
        tvdb.episodes(show)
        tvdb.episodes(show)
        self.assertEqual(client.all_episodes.call_count, 2)

    def test_episode_cache_max_shows_bound(self):
        """Cache cannot grow unbounded across many shows for process lifetime."""
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.all_episodes.return_value = [
            {"id": 1, "seasonNumber": 1, "number": 1, "name": "One", "lastUpdated": 100},
        ]
        tvdb._episode_cache_max_shows = 2
        for show_id in (101, 102, 103):
            show = MagicMock()
            show.indexerid = show_id
            show.dvdorder = False
            show.lang = "en"
            tvdb.episodes(show)
        # List and index caches both stay within the unique-show bound; oldest (101) is evicted
        unique_list_shows = {key[0] for key in tvdb._episode_list_cache}
        unique_index_shows = {key[0] for key in tvdb._episode_index_cache}
        self.assertLessEqual(len(unique_list_shows), tvdb._episode_cache_max_shows)
        self.assertLessEqual(len(unique_index_shows), tvdb._episode_cache_max_shows)
        self.assertNotIn(101, unique_list_shows)
        self.assertNotIn(101, unique_index_shows)

    def test_episodes_uses_show_lang_and_separates_cache(self):
        """Japanese primary titles must not stick when show.lang is English (Dungeon Meshi case)."""
        tvdb = TVDB()
        client = attach_mock_client(tvdb)

        def all_episodes(show_id, season_type="default", max_pages=50, language=None):
            if language == "eng":
                return [{"id": 1, "seasonNumber": 1, "number": 1, "name": "Hot Pot", "lastUpdated": 100}]
            if language == "jpn":
                return [{"id": 1, "seasonNumber": 1, "number": 1, "name": "水炊き", "lastUpdated": 100}]
            return [{"id": 1, "seasonNumber": 1, "number": 1, "name": "水炊き", "lastUpdated": 100}]

        client.all_episodes.side_effect = all_episodes
        show = MagicMock()
        show.indexerid = 423257
        show.dvdorder = False

        show.lang = "en"
        en_eps = tvdb.episodes(show)
        self.assertEqual(en_eps[0]["episodeName"], "Hot Pot")

        show.lang = "ja"
        ja_eps = tvdb.episodes(show)
        self.assertEqual(ja_eps[0]["episodeName"], "水炊き")
        # Separate cache entries per language (second call is not a cache hit of English)
        self.assertGreaterEqual(client.all_episodes.call_count, 2)

    def test_client_series_episodes_translated_path(self):
        client = TVDBv4Client("test-key")
        with patch.object(client, "_get", return_value={"episodes": []}) as mock_get:
            client.series_episodes(423257, "default", page=0, language="eng")
            path = mock_get.call_args[0][0]
            self.assertEqual(path, "/series/423257/episodes/default/eng")

        with patch.object(client, "_get", return_value={"episodes": []}) as mock_get:
            client.series_episodes(423257, "default", page=0, language=None)
            path = mock_get.call_args[0][0]
            self.assertEqual(path, "/series/423257/episodes/default")


class UpdatesFeedOkTests(unittest.TestCase):
    def test_feed_ok_false_when_all_entity_types_fail(self):
        client = MagicMock()
        client.all_updates_since.side_effect = TVDBv4Error("down")
        updates = _UpdatesResult(client, from_time=1000)
        result = updates.series()
        self.assertEqual(result, [])
        self.assertFalse(updates.feed_ok)

    def test_feed_ok_true_on_empty_success(self):
        client = MagicMock()
        client.all_updates_since.return_value = []
        updates = _UpdatesResult(client, from_time=1000)
        result = updates.series()
        self.assertEqual(result, [])
        self.assertTrue(updates.feed_ok)

    def test_feed_ok_false_on_partial_entity_failure(self):
        """Partial feed (one entity type fails) must not report success or advance lastUpdate."""
        client = MagicMock()

        def all_updates_since(since, entity_type="series", max_pages=50):
            if entity_type == "series":
                return []  # empty success
            raise TVDBv4Error("episodes feed down")

        client.all_updates_since.side_effect = all_updates_since
        updates = _UpdatesResult(client, from_time=1000)
        result = updates.series()
        self.assertEqual(result, [])
        self.assertFalse(updates.feed_ok)

    def test_feed_ok_false_when_series_fails_episodes_ok(self):
        """Either entity-type failure keeps feed_ok False (symmetric to episodes failing)."""
        client = MagicMock()

        def all_updates_since(since, entity_type="series", max_pages=50):
            if entity_type == "series":
                raise TVDBv4Error("series feed down")
            return [{"recordType": "episode", "seriesId": 42, "id": 1}]

        client.all_updates_since.side_effect = all_updates_since
        updates = _UpdatesResult(client, from_time=1000)
        result = updates.series()
        self.assertEqual(result, [])
        self.assertFalse(updates.feed_ok)


class EpisodeSkipApplyTests(unittest.TestCase):
    def test_load_from_indexer_skips_when_last_updated_not_newer(self):
        from sickchill.tv import TVEpisode

        ep = MagicMock(spec=TVEpisode)
        # Bind real method
        ep.last_update_indexer = 500
        ep.name = "Old"
        ep.show = MagicMock()
        ep.show.indexerid = 1
        ep.show.name = "Show"
        ep.season = 1
        ep.episode = 1
        ep.indexer_name = "theTVDB"
        ep.idxr = MagicMock()

        packet = {
            "episodeName": "New Title",
            "lastUpdated": 400,  # older than stored
            "absoluteNumber": 1,
            "overview": "x",
            "firstAired": "2020-01-01",
            "id": 99,
        }

        # Call unbound method with a simple object that has required attrs
        class E:
            pass

        e = E()
        e.last_update_indexer = 500
        e.name = "Old"
        e.show = MagicMock()
        e.show.indexerid = 1
        e.show.name = "Show"
        e.season = 1
        e.episode = 1
        e.indexer_name = "theTVDB"
        e.idxr = MagicMock()
        e.dirty = False

        result = TVEpisode.load_from_indexer(e, 1, 1, force_all=False, indexer_episode=packet)
        self.assertTrue(result)
        self.assertEqual(e.name, "Old")  # not applied

    def test_apply_tba_indexer_packet_sets_name_and_last_update(self):
        from sickchill.tv import TVEpisode

        class E:
            pass

        e = E()
        e.name = "TBA"
        e.description = ""
        e.airdate = datetime.date(1, 1, 1)
        e.absolute_number = 0
        e.indexerid = 0
        e.last_update_indexer = 0
        e.season = 1
        e.episode = 2
        e.show = MagicMock()
        e.show.name = "Show"

        packet = {
            "episodeName": "Real Title",
            "overview": "Plot",
            "firstAired": "2024-01-15",
            "absoluteNumber": 12,
            "id": 999,
            "lastUpdated": 1700000000,
        }
        changed = TVEpisode.apply_tba_indexer_packet(e, packet)
        self.assertIn("name", changed)
        self.assertIn("airdate", changed)
        self.assertIn("absolute_number", changed)
        self.assertEqual(e.name, "Real Title")
        self.assertEqual(e.description, "Plot")
        self.assertEqual(e.airdate, datetime.date(2024, 1, 15))
        self.assertEqual(e.absolute_number, 12)
        self.assertEqual(e.last_update_indexer, 1700000000)
        self.assertEqual(e.indexerid, 999)

    def test_apply_tba_skips_when_still_tba(self):
        from sickchill.tv import TVEpisode

        class E:
            name = "TBA"

        self.assertEqual(TVEpisode.apply_tba_indexer_packet(E(), {"episodeName": "TBA"}), [])


class MassActionSqlCollectionTests(unittest.TestCase):
    """Regression: get_sql() shape must be appended, not extended, into mass_action lists."""

    @staticmethod
    def _fake_get_sql(name: str, ep_id: int):
        """Shape matches TVEpisode.get_sql(): [statement:str, params:list]."""
        return [
            "UPDATE tv_episodes SET name = ? WHERE episode_id = ?",
            [name, ep_id],
        ]

    def test_get_sql_unit_is_statement_plus_params(self):
        """get_sql returns a two-element [query, params] mass_action unit."""
        sql_unit = self._fake_get_sql("エリスのゴブリン討伐", 2868)
        self.assertEqual(len(sql_unit), 2)
        self.assertIsInstance(sql_unit[0], str)
        self.assertTrue(sql_unit[0].lstrip().upper().startswith("UPDATE"))
        self.assertIsInstance(sql_unit[1], list)
        self.assertEqual(len(sql_unit[1]), 2)

    def test_append_keeps_mass_action_units_intact(self):
        """Appending get_sql units yields [[stmt, params], ...]; extend flattens and breaks mass_action."""
        sql_l = []
        for name, ep_id in (("無職転生", 1), ("師匠", 2)):
            sql = self._fake_get_sql(name, ep_id)
            if sql:
                sql_l.append(sql)

        self.assertEqual(len(sql_l), 2)
        for qu in sql_l:
            self.assertEqual(len(qu), 2)
            self.assertIsInstance(qu[0], str)
            self.assertTrue(qu[0].lstrip().upper().startswith("UPDATE"))
            self.assertIsInstance(qu[1], list)

        # mass_action path receives intact units
        db_mock = MagicMock()
        db_mock.mass_action(sql_l)
        db_mock.mass_action.assert_called_once_with(sql_l)

        # Document the broken extend path that caused: near "U": syntax error
        broken = []
        for unit in sql_l:
            broken.extend(unit)
        self.assertEqual(len(broken), 4)
        self.assertEqual(broken[0][0], "U")


class WebHandlerDisconnectTests(unittest.IsolatedAsyncioTestCase):
    """Regression: aborted/disconnected clients must not auto-finish via Tornado."""

    async def test_client_disconnected_disables_auto_finish(self):
        from unittest.mock import AsyncMock

        from sickchill import settings
        from sickchill.views.index import WebHandler

        handler = object.__new__(WebHandler)
        handler._auto_finish = True
        handler._finished = False
        handler.request = MagicMock()
        handler.request.connection = MagicMock()
        handler.request.connection.stream = MagicMock()
        handler.request.connection.stream.closed.return_value = True

        # Bypass @authenticated — invoke the wrapped coroutine body via __wrapped__ if present
        get_method = WebHandler.get
        if hasattr(get_method, "__wrapped__"):
            get_method = get_method.__wrapped__

        with (
            patch.object(WebHandler, "async_call", new_callable=AsyncMock) as mock_call,
            patch.object(settings, "DEVELOPER", False),
        ):
            mock_call.return_value = "<html>page</html>"
            # Provide a dummy route method so getattr(self, route) succeeds
            handler.index = MagicMock()
            result = await get_method(handler, "index")

        self.assertIsNone(result)
        # Tornado must not auto-call finish() after we return from a disconnected request
        self.assertFalse(handler._auto_finish)


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

    def test_map_search_results_uses_metadata_language_translation(self):
        """addShows list should show eng/ita/etc. title, not original primary (e.g. ダンジョン飯)."""
        raw = [
            {
                "tvdb_id": "series-423257",
                "name": "ダンジョン飯",
                "primary_language": "jpn",
                "first_air_time": "2024-01-04",
                "overview": "Japanese overview",
                "translations": {
                    "eng": "Delicious in Dungeon",
                    "jpn": "ダンジョン飯",
                    "ita": "Delicious in Dungeon",
                },
                "overviews": {
                    "eng": "English overview of the dungeon adventure.",
                    "jpn": "Japanese overview",
                },
            }
        ]
        mapped_en = TVDB._map_search_results(raw, language="en")
        self.assertEqual(mapped_en[0]["id"], 423257)
        self.assertEqual(mapped_en[0]["seriesName"], "Delicious in Dungeon")
        self.assertEqual(mapped_en[0]["overview"], "English overview of the dungeon adventure.")

        mapped_ja = TVDB._map_search_results(raw, language="ja")
        self.assertEqual(mapped_ja[0]["seriesName"], "ダンジョン飯")

        # Without language, keep primary/original title
        mapped_default = TVDB._map_search_results(raw)
        self.assertEqual(mapped_default[0]["seriesName"], "ダンジョン飯")

    def test_client_search_does_not_filter_by_primary_language(self):
        """/search?language= restricts primary language — must not be sent for UI metadata lang."""
        from sickchill.show.indexers.tvdb_v4_client import TVDBv4Client

        client = TVDBv4Client("test-key")
        with patch.object(client, "_get", return_value=[]) as mock_get:
            client.search("delicious in dungeon", language="en")
            mock_get.assert_called_once()
            path = mock_get.call_args.args[0]
            params = mock_get.call_args.kwargs.get("params") or {}
            self.assertEqual(path, "/search")
            self.assertNotIn("language", params)
            self.assertEqual(params.get("query"), "delicious in dungeon")
            self.assertEqual(params.get("type"), "series")

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

    def test_map_search_results_normalizes_score(self):
        raw = [
            {"tvdb_id": "1", "name": "Best", "score": 200},
            {"tvdb_id": "2", "name": "Mid", "score": 100},
            {"tvdb_id": "3", "name": "Low", "score": 50},
        ]
        mapped = TVDB._map_search_results(raw)
        self.assertEqual(mapped[0]["score"], 100)  # 200/200 * 100
        self.assertEqual(mapped[1]["score"], 50)  # 100/200 * 100
        self.assertEqual(mapped[2]["score"], 25)  # 50/200 * 100
        self.assertTrue(all(isinstance(m["score"], int) for m in mapped))
        self.assertEqual(mapped[0]["source"], "tvdb")

    def test_map_search_results_score_from_api_order_when_missing(self):
        raw = [
            {"tvdb_id": "1", "name": "First"},
            {"tvdb_id": "2", "name": "Second"},
        ]
        mapped = TVDB._map_search_results(raw)
        # No raw scores → first hit highest (100), second lower
        self.assertEqual(mapped[0]["score"], 100)
        self.assertEqual(mapped[1]["score"], 50)
        self.assertTrue(all(isinstance(m["score"], int) for m in mapped))


class SeasonsOrderTests(unittest.TestCase):
    def test_resolve_season_type_from_seasons_order(self):
        show = MagicMock()
        show.resolved_seasons_order = "absolute"
        self.assertEqual(TVDB.resolve_season_type(show), "absolute")

    def test_resolve_season_type_legacy_dvdorder(self):
        class S:
            dvdorder = 1

        self.assertEqual(TVDB.resolve_season_type(S()), "dvd")

        class S2:
            dvdorder = 0
            seasons_order = "official"

        self.assertEqual(TVDB.resolve_season_type(S2()), "official")

    def test_fetch_series_season_types_from_extended(self):
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.series_extended.return_value = {
            "seasonTypes": [
                {"type": "default", "name": "Aired Order"},
                {"type": "dvd", "name": "DVD Order", "alternateName": "DVD"},
                {"type": "absolute", "name": "Absolute Order"},
            ],
            "seasons": [],
        }
        client.season_types_catalog.return_value = []
        types = tvdb._fetch_series_season_types(99)
        by_slug = {t["slug"]: t["name"] for t in types}
        self.assertEqual(by_slug["default"], "Aired Order")
        self.assertEqual(by_slug["dvd"], "DVD")  # alternateName preferred
        self.assertEqual(by_slug["absolute"], "Absolute Order")

    def test_fetch_series_season_types_collapses_official_and_default(self):
        """TVDB may return both default and official as aired — only one option; platform names stay series-specific."""
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.series_extended.return_value = {
            "seasonTypes": [
                {"type": "official", "name": "Aired Order", "alternateName": "Aired"},
                {"type": "default", "name": "Aired Order"},
                {"type": "dvd", "name": "DVD Order"},
                {"type": "absolute", "name": "Absolute Order"},
                # slug "alternate" is generic; display name is whatever TVDB gives this series
                {"type": "alternate", "name": "Alternate Order", "alternateName": "BBC iPlayer"},
                # Distinct path slugs are never merged (another platform order on the same show)
                {"type": "altdvd", "name": "Alternate DVD", "alternateName": "Netflix"},
            ],
            "seasons": [],
        }
        types = tvdb._fetch_series_season_types(78804)
        slugs = [t["slug"] for t in types]
        by_slug = {t["slug"]: t["name"] for t in types}
        self.assertEqual(slugs.count("default"), 1)
        self.assertNotIn("official", slugs)
        self.assertEqual(by_slug["default"], "Aired Order")
        self.assertEqual(by_slug["absolute"], "Absolute Order")
        self.assertEqual(by_slug["alternate"], "BBC iPlayer")
        self.assertEqual(by_slug["altdvd"], "Netflix")
        self.assertEqual(len(types), len(set(slugs)))

    def test_seasons_order_label_is_series_specific(self):
        """Same slug can show different labels on different series (platform-named orders)."""
        tvdb = TVDB()
        with patch.object(
            tvdb,
            "series_season_types",
            return_value=[
                {"slug": "default", "name": "Aired Order"},
                {"slug": "alternate", "name": "BBC iPlayer"},
            ],
        ):
            self.assertEqual(tvdb.seasons_order_label(1, "default"), "Aired Order")
            self.assertEqual(tvdb.seasons_order_label(1, "alternate"), "BBC iPlayer")
            self.assertEqual(tvdb.seasons_order_label(1, "official"), "Aired Order")

        with patch.object(
            tvdb,
            "series_season_types",
            return_value=[
                {"slug": "default", "name": "Aired Order"},
                {"slug": "alternate", "name": "Some Other Platform"},
            ],
        ):
            self.assertEqual(tvdb.seasons_order_label(2, "alternate"), "Some Other Platform")

    def test_episodes_uses_seasons_order(self):
        tvdb = TVDB()
        client = attach_mock_client(tvdb)
        client.all_episodes.return_value = [
            {"id": 1, "seasonNumber": 1, "number": 1, "name": "One", "lastUpdated": 1},
        ]

        class Show:
            indexerid = 42
            dvdorder = 0
            seasons_order = "absolute"
            lang = "en"

            @property
            def resolved_seasons_order(self):
                return self.seasons_order

        tvdb.episodes(Show())
        args, kwargs = client.all_episodes.call_args
        # all_episodes(show_id, season_type, language=code)
        self.assertEqual(args[1] if len(args) > 1 else kwargs.get("season_type"), "absolute")


if __name__ == "__main__":
    unittest.main()
