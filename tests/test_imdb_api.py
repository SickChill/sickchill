"""IMDb client: tt ids, popular-show cards, and imdb_info fields."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard.imdb_api import Imdb, ImdbFacade
from sickchill.show.recommendations.imdb import imdbPopular
from sickchill.tv import TVShow


class ImdbTitleMappingTests(unittest.TestCase):
    def test_facade_maps_fields_used_by_load_imdb_info(self):
        client = MagicMock()
        client.get_title.return_value = {
            "base": {"title": "Game of Thrones", "year": 2011, "titleType": "tvSeries"},
            "ratings": {"rating": 9.2, "ratingCount": 2100000},
        }
        client.get_title_auxiliary.return_value = {
            "id": "/title/tt0944947/",
            "runningTimes": [{"timeMinutes": 57}],
            "genres": ["Drama", "Adventure"],
            "certificate": {"certificate": "TV-MA"},
        }
        title = ImdbFacade(client=client).get_title("tt0944947")
        self.assertEqual(title.imdb_id, "tt0944947")
        self.assertEqual(title.title, "Game of Thrones")
        self.assertEqual(title.year, 2011)
        self.assertEqual(title.runtime, 57)
        self.assertEqual(title.genres, ("drama", "adventure"))
        self.assertEqual(title.certification, "TV-MA")
        self.assertEqual(title.rating, 9.2)
        self.assertEqual(title.rating_count, 2100000)

        show = object.__new__(TVShow)
        show.indexerid = 121361
        show.imdb_id = "tt0944947"
        show.name = "Game of Thrones"
        show.startyear = 2011
        show.runtime = 0
        show.imdb_info = {}
        show.imdb_info.update(
            {
                "indexer_id": show.indexerid,
                "imdb_id": title.imdb_id,
                "title": title.title,
                "year": title.year,
                "runtimes": title.runtime,
                "genres": "|".join(title.genres or []),
                "certificates": title.certification or "",
                "rating": str(title.rating),
                "votes": str(title.rating_count),
            }
        )
        self.assertEqual(show.imdb_info["imdb_id"], "tt0944947")
        self.assertEqual(show.imdb_info["title"], "Game of Thrones")
        self.assertEqual(show.imdb_info["genres"], "drama|adventure")
        self.assertEqual(show.imdb_info["votes"], "2100000")

    def test_eight_digit_tt_id_is_valid(self):
        Imdb.validate_imdb_id("tt41154853")
        Imdb.validate_imdb_id("tt0944947")
        with self.assertRaises(ValueError):
            Imdb.validate_imdb_id("not-an-id")


class ImdbSearchAndPopularTests(unittest.TestCase):
    def test_search_for_title_keeps_tt_results(self):
        client = Imdb()
        payload = {
            "d": [
                {"l": "Game of Thrones", "id": "tt0944947", "q": "TV series", "y": 2011},
                {"l": "Some Person", "id": "nm0000001"},
            ]
        }
        with patch.object(client, "_get", return_value=payload):
            results = client.search_for_title("Game of Thrones")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["imdb_id"], "tt0944947")
        self.assertEqual(results[0]["type"], "TV series")
        self.assertTrue(any(token in results[0]["type"].lower() for token in ("tv", "series")))

    def test_popular_shows_ranks_keep_tt_and_display_fields(self):
        client = MagicMock()
        client.get_popular_shows.return_value = {
            "ranks": [
                {
                    "id": "/title/tt0944947/",
                    "tconst": "tt0944947",
                    "title": "Game of Thrones",
                    "year": 2011,
                    "image": {"url": "https://img.example/got.jpg"},
                    "currentRank": 1,
                },
                {"title": "missing-id"},
            ]
        }
        popular = imdbPopular()
        popular.client = client
        rows = popular.fetch_popular_shows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["tconst"], "tt0944947")

        # Same cleaning Add Shows /popularShows uses
        show = rows[0]
        imdb_id = show.get("id") or show.get("tconst")
        if isinstance(imdb_id, str) and imdb_id.startswith("/title/"):
            imdb_id = imdb_id.split("/")[2]
        self.assertEqual(imdb_id, "tt0944947")
        self.assertEqual(show.get("title") or show.get("l"), "Game of Thrones")
        self.assertEqual(show["image"]["url"], "https://img.example/got.jpg")
