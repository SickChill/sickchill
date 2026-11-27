"""IMDb client: tt ids, popular-show cards, and imdb_info fields."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sickchill.show.indexers.imdb_api import Imdb, ImdbFacade, _creds_need_refresh, _creds_path
from sickchill.show.recommendations.imdb import (
    allowed_poster_url,
    imdbPopular,
    poster_cache_name,
    poster_cache_path,
    sized_poster_url,
)


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

    def test_empty_title_payload_returns_none(self):
        client = MagicMock()
        client.get_title.return_value = {}
        client.get_title_auxiliary.return_value = {"genres": ["Drama"]}
        self.assertIsNone(ImdbFacade(client=client).get_title("tt0944947"))

    def test_creds_path_avoids_shared_tempdir(self):
        with patch("sickchill.settings.CACHE_DIR", None):
            path = _creds_path()
        self.assertNotEqual(Path(path).parent.resolve(), Path(tempfile.gettempdir()).resolve())

    def test_incomplete_cached_creds_need_refresh(self):
        self.assertTrue(_creds_need_refresh(None))
        self.assertTrue(_creds_need_refresh({"expirationTimeStamp": "2099-01-01T00:00:00Z"}))
        self.assertTrue(
            _creds_need_refresh(
                {
                    "expirationTimeStamp": "2099-01-01T00:00:00Z",
                    "accessKeyId": "AKID",
                    "secretAccessKey": "",
                }
            )
        )

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


_AMAZON = "https://m.media-amazon.com/images/M/MV5BZWYwZTZiZGEtNjBlOS00MGEzLWI3MmUtMTRhMWM4NzAwYTQ1XkEyXkFqcGc@._V1_.jpg"


class ImdbPosterCacheTests(unittest.TestCase):
    def test_sized_poster_url_requests_a_card_jpeg(self):
        self.assertEqual(sized_poster_url(_AMAZON), _AMAZON.replace("@._V1_.jpg", "@._V1_QL75_UX280_.jpg"))

    def test_poster_url_allowlist(self):
        self.assertTrue(allowed_poster_url(_AMAZON))
        self.assertTrue(allowed_poster_url(sized_poster_url(_AMAZON)))
        self.assertFalse(allowed_poster_url("http://m.media-amazon.com/images/M/x.jpg"))
        self.assertFalse(allowed_poster_url("https://evil.example/images/M/x.jpg"))
        self.assertFalse(allowed_poster_url("https://user:pass@m.media-amazon.com/images/M/x.jpg"))
        self.assertFalse(allowed_poster_url("https://m.media-amazon.com/other/x.jpg"))

    def test_poster_cache_name_rejects_path_tricks(self):
        self.assertEqual(poster_cache_name("tt0944947"), "tt0944947.jpg")
        self.assertEqual(poster_cache_name("tt41154853"), "tt41154853.jpg")
        self.assertIsNone(poster_cache_name("tt0944947/../../etc/passwd"))
        self.assertIsNone(poster_cache_name("../tt0944947"))

    def test_cache_poster_writes_jpeg_and_skips_a_second_download(self):
        class Response:
            def __init__(self):
                self.status_code = 200
                self.headers = {"Content-Type": "image/jpeg"}

            def iter_content(self, _chunk_size):
                yield b"\xff\xd8\xff\xd9"

            def close(self):
                return None

        popular = imdbPopular()
        popular.session = MagicMock()
        popular.session.get.return_value = Response()
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch("sickchill.show.recommendations.imdb.settings.CACHE_DIR", cache_dir):
                self.assertTrue(popular.cache_poster("tt0944947", _AMAZON))
                stored = Path(poster_cache_path("tt0944947")).read_bytes()
                self.assertEqual(stored, b"\xff\xd8\xff\xd9")
                popular.session.get.assert_called_once()
                requested = popular.session.get.call_args.args[0]
                self.assertTrue(requested.endswith("@._V1_QL75_UX280_.jpg"))
                self.assertFalse(popular.session.get.call_args.kwargs["allow_redirects"])
                self.assertTrue(popular.cache_poster("tt0944947", _AMAZON))
                popular.session.get.assert_called_once()

    def test_cache_poster_rejects_a_redirect(self):
        class Response:
            def __init__(self):
                self.status_code = 302
                self.headers = {"Location": "http://127.0.0.1/secret", "Content-Type": "image/jpeg"}

            def iter_content(self, _chunk_size):
                yield b"\xff\xd8\xff\xd9"

            def close(self):
                return None

        popular = imdbPopular()
        popular.session = MagicMock()
        popular.session.get.return_value = Response()
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch("sickchill.show.recommendations.imdb.settings.CACHE_DIR", cache_dir):
                self.assertFalse(popular.cache_poster("tt0944947", _AMAZON))
                self.assertFalse(Path(cache_dir, "images", "imdb_popular", "tt0944947.jpg").exists())
