"""Unit tests for TMDB / TVMaze Add Shows discovery helpers (mocked HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.helper.list_status import build_list_status
from sickchill.oldbeard import tmdbLists, tvmazePremieres
from sickchill.views.manage.add_shows import AddShows


class ListStatusTests(unittest.TestCase):
    def test_missing_key_and_empty(self):
        missing = build_list_status("missing_key", settings_url="/config/general/")
        self.assertEqual(missing["code"], "missing_key")
        self.assertTrue(missing["settings_url"])

        empty = build_list_status("empty")
        self.assertEqual(empty["code"], "empty")

        ok = build_list_status(None)
        self.assertEqual(ok["code"], "ok")


class TMDBListsTests(unittest.TestCase):
    def setUp(self):
        tmdbLists.clear_cache()

    @patch("sickchill.oldbeard.tmdbLists._api_key", return_value="")
    def test_missing_key(self, _key):
        with self.assertRaises(tmdbLists.TMDBMissingKeyError):
            tmdbLists.fetch_list("trending")

    @patch("sickchill.oldbeard.tmdbLists._api_key", return_value="test-key")
    @patch("sickchill.oldbeard.tmdbLists.helpers.getURL")
    def test_fetch_list_normalizes_cards(self, get_url, _key):
        get_url.return_value = {
            "results": [
                {
                    "id": 1399,
                    "name": "Game of Thrones",
                    "overview": "Winter is coming",
                    "poster_path": "/got.jpg",
                    "first_air_date": "2011-04-17",
                    "vote_average": 8.4,
                    "vote_count": 1000,
                },
                {"id": None, "name": "skip"},
            ]
        }
        cards = tmdbLists.fetch_list("trending")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["tmdb_id"], 1399)
        self.assertEqual(cards[0]["title"], "Game of Thrones")
        self.assertEqual(cards[0]["year"], 2011)
        self.assertTrue(cards[0]["poster_url"].endswith("/got.jpg"))
        self.assertEqual(cards[0]["source"], "tmdb")
        # Second call hits cache — getURL once
        tmdbLists.fetch_list("trending")
        self.assertEqual(get_url.call_count, 1)

    @patch("sickchill.oldbeard.tmdbLists._api_key", return_value="test-key")
    @patch("sickchill.oldbeard.tmdbLists.helpers.getURL")
    def test_resolve_tvdb_id(self, get_url, _key):
        get_url.return_value = {"tvdb_id": 121361, "imdb_id": "tt0944947"}
        self.assertEqual(tmdbLists.resolve_tvdb_id(1399), 121361)

        get_url.return_value = {"tvdb_id": None}
        self.assertIsNone(tmdbLists.resolve_tvdb_id(1))


class TVMazePremieresTests(unittest.TestCase):
    def setUp(self):
        tvmazePremieres.clear_cache()

    @patch("sickchill.oldbeard.tvmazePremieres.helpers.getURL")
    def test_filters_s01e01_and_dedupes(self, get_url):
        get_url.return_value = [
            {
                "season": 1,
                "number": 1,
                "airdate": "2026-09-15",
                "_embedded": {
                    "show": {
                        "id": 10,
                        "name": "New Show",
                        "summary": "<p>Hello</p>",
                        "premiered": "2026-01-01",
                        "image": {"medium": "https://example.com/a.jpg"},
                        "externals": {"thetvdb": 999},
                        "rating": {"average": 7.5},
                        "language": "English",
                        "url": "https://www.tvmaze.com/shows/10",
                    }
                },
            },
            {
                "season": 1,
                "number": 1,
                "_embedded": {
                    "show": {
                        "id": 10,
                        "name": "New Show Dup",
                        "externals": {"thetvdb": 999},
                    }
                },
            },
            {
                "season": 2,
                "number": 1,
                "_embedded": {"show": {"id": 11, "name": "Not Premiere"}},
            },
            {
                "season": 1,
                "number": 2,
                "_embedded": {"show": {"id": 12, "name": "Not Pilot"}},
            },
        ]
        cards = tvmazePremieres.fetch_premieres()
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["tvmaze_id"], 10)
        self.assertEqual(cards[0]["tvdb_id"], 999)
        self.assertEqual(cards[0]["overview"], "Hello")
        self.assertEqual(cards[0]["airdate"], "2026-09-15")
        self.assertEqual(cards[0]["language"], "English")
        self.assertEqual(cards[0]["rating"], 7.5)
        self.assertEqual(cards[0]["source"], "tvmaze")


class DiscoveryListKeyTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(AddShows._resolve_discovery_list_key("anticipated"), "trending")
        self.assertEqual(AddShows._resolve_discovery_list_key("newshow"), "premieres")
        self.assertEqual(AddShows._resolve_discovery_list_key("traktList-bogus"), "trending")
        self.assertEqual(AddShows._resolve_discovery_list_key("top_rated"), "top_rated")

    def test_trakt_list_keys(self):
        self.assertEqual(AddShows._resolve_trakt_list_key("anticipated"), "anticipated")
        self.assertEqual(AddShows._resolve_trakt_list_key("trending"), "trending")
        self.assertEqual(AddShows._resolve_trakt_list_key("bogus"), "anticipated")

    def test_discovery_source_from_query(self):
        class FakeHandler:
            def __init__(self, args):
                self._args = args

            def get_query_argument(self, name, default=""):
                return self._args.get(name, default)

        self.assertEqual(
            AddShows._discovery_source_from_query(FakeHandler({"tmdbList": "popular"})),
            ("tmdb", "popular"),
        )
        self.assertEqual(
            AddShows._discovery_source_from_query(FakeHandler({"traktList": "anticipated"})),
            ("trakt", "anticipated"),
        )
        # Both present: tmdb wins (legacy JS wrote both)
        self.assertEqual(
            AddShows._discovery_source_from_query(FakeHandler({"tmdbList": "trending", "traktList": "anticipated"})),
            ("tmdb", "trending"),
        )
        self.assertEqual(
            AddShows._discovery_source_from_query(FakeHandler({})),
            ("tmdb", "trending"),
        )


class ListStatusTraktTests(unittest.TestCase):
    def test_trakt_fetch_failed_mentions_auth(self):
        status = build_list_status("fetch_failed", settings_url="/config/general/", source="trakt")
        self.assertEqual(status["code"], "fetch_failed")
        self.assertIn("Trakt", status["title"])
        self.assertTrue(status["settings_url"])


class TraktAlreadyAddedTests(unittest.TestCase):
    @patch("sickchill.views.manage.add_shows.settings")
    def test_mark_trakt_already_added(self, mock_settings):
        show = MagicMock()
        show.indexerid = 121361
        mock_settings.show_list = [show]
        cards = [
            {"show": {"title": "GoT", "ids": {"tvdb": 121361}}},
            {"show": {"title": "Other", "ids": {"tvdb": 1}}},
        ]
        AddShows._mark_trakt_already_added(cards)
        self.assertTrue(cards[0]["already_added"])
        self.assertFalse(cards[1]["already_added"])


if __name__ == "__main__":
    unittest.main()
