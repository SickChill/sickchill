"""Phase 1: list_propers SQL scopes to provider; proper search watermark."""

from __future__ import annotations

import datetime
import re
import time
import unittest
from unittest import mock

from sickchill.oldbeard import db
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone
from sickchill.oldbeard.properFinder import ProperFinder
from sickchill.oldbeard.tvcache import TVCache
from tests import conftest


class _FakeProvider:
    def __init__(self, provider_id="testprovider"):
        self.id = provider_id
        self.name = provider_id
        self.proper_strings = ["PROPER|REPACK|REAL"]

    def get_id(self):
        return self.id


class TestListPropersSQL(conftest.SickChillTestDBCase):
    def setUp(self):
        super().setUp()
        self.cache_db = db.DBConnection("cache.db")
        self.provider_a = "propers_provider_a"
        self.provider_b = "propers_provider_b"
        self.cache_db.action("DELETE FROM results WHERE provider IN (?, ?)", [self.provider_a, self.provider_b])

    def tearDown(self):
        self.cache_db.action("DELETE FROM results WHERE provider IN (?, ?)", [self.provider_a, self.provider_b])
        super().tearDown()

    def _insert(self, provider, name, indexerid=12345, age_hours=1):
        ts = int(time.time()) - int(age_hours * 3600)
        self.cache_db.action(
            "INSERT OR IGNORE INTO results (provider, name, season, episodes, indexerid, url, time, quality, release_group, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [provider, name, 1, "|1|", indexerid, f"http://example/{provider}/{name}", ts, "HD", "", -1],
        )

    def test_list_propers_scoped_to_provider(self):
        self._insert(self.provider_a, "Show.S01E01.PROPER.720p.HDTV")
        self._insert(self.provider_b, "Other.S01E01.REPACK.720p.HDTV")

        provider = _FakeProvider(self.provider_a)
        cache = TVCache(provider)
        # TVCache may derive provider_id from provider.get_id()
        rows = cache.list_propers(date=None)
        names = {r["name"] for r in rows}
        self.assertIn("Show.S01E01.PROPER.720p.HDTV", names)
        self.assertNotIn("Other.S01E01.REPACK.720p.HDTV", names)

    def test_list_propers_includes_real_and_date_filter(self):
        self._insert(self.provider_a, "Show.S01E02.REAL.1080p.WEB", age_hours=1)
        self._insert(self.provider_a, "Show.S01E03.PROPER.1080p.WEB", age_hours=48)

        provider = _FakeProvider(self.provider_a)
        cache = TVCache(provider)
        since = sc_now() - datetime.timedelta(hours=6)
        rows = cache.list_propers(date=since)
        names = {r["name"] for r in rows}
        self.assertIn("Show.S01E02.REAL.1080p.WEB", names)
        self.assertNotIn("Show.S01E03.PROPER.1080p.WEB", names)

    def test_list_propers_matches_hyphenated_proper_group_suffix(self):
        """Leading '.' before PROPER retained; trailing -GRP (release group) allowed."""
        self._insert(self.provider_a, "Show.S01E01.PROPER-GRP.720p.HDTV")
        self._insert(self.provider_a, "Show.S01E01.REPACK-GROUP.1080p.WEB")
        self._insert(self.provider_a, "Show.S01E01.NOPROPERHERE.720p.HDTV")  # no .PROPER delimiter

        provider = _FakeProvider(self.provider_a)
        cache = TVCache(provider)
        rows = cache.list_propers(date=None)
        names = {r["name"] for r in rows}
        self.assertIn("Show.S01E01.PROPER-GRP.720p.HDTV", names)
        self.assertIn("Show.S01E01.REPACK-GROUP.1080p.WEB", names)
        self.assertNotIn("Show.S01E01.NOPROPERHERE.720p.HDTV", names)


class TestProperSearchDate(unittest.TestCase):
    def test_defaults_to_two_day_floor_when_never_run(self):
        finder = ProperFinder()
        with mock.patch.object(finder, "_get_last_proper_search", return_value=datetime.date.min):
            with mock.patch("sickchill.oldbeard.properFinder.sc_now") as now_mock:
                fixed = datetime.datetime(2026, 9, 4, 15, 0, 0, tzinfo=sc_timezone)
                now_mock.return_value = fixed
                got = finder._proper_search_date()
        self.assertEqual(got, fixed - datetime.timedelta(days=2))

    def test_uses_last_proper_search_minus_overlap(self):
        finder = ProperFinder()
        last = datetime.date(2026, 9, 3)
        with mock.patch.object(finder, "_get_last_proper_search", return_value=last):
            with mock.patch("sickchill.oldbeard.properFinder.sc_now") as now_mock:
                fixed = datetime.datetime(2026, 9, 4, 15, 0, 0, tzinfo=sc_timezone)
                now_mock.return_value = fixed
                got = finder._proper_search_date()
        expected = datetime.datetime.combine(last, datetime.time(), tzinfo=sc_timezone) - datetime.timedelta(hours=6)
        self.assertEqual(got, expected)


class TestProperSearchAddString(unittest.TestCase):
    def test_collapses_separate_terms(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("x")
        provider.proper_strings = ["PROPER", "REPACK", "REAL"]
        self.assertEqual(provider.proper_search_add_string(), "PROPER|REPACK|REAL")

    def test_already_ored_string(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("x")
        provider.proper_strings = ["PROPER|REPACK|REAL"]
        self.assertEqual(provider.proper_search_add_string(), "PROPER|REPACK|REAL")


def _proper_candidate(name, indexerid, season, episode, resource, anime=False, absolute=None):
    show = mock.Mock()
    show.indexerid = indexerid
    show.name = name
    show.air_by_date = False
    show.sports = False
    show.anime = 1 if anime else 0
    show.is_anime = anime
    ep = mock.Mock()
    ep.show = show
    ep.season = season
    ep.scene_season = season
    ep.episode = episode
    ep.scene_episode = episode
    ep.scene_absolute_number = absolute if absolute is not None else episode
    return show, ep, resource


def _queries(provider):
    queries = []
    for call in provider.search.call_args_list:
        for values in call[0][0].values():
            queries.extend(values)
    return queries


class TestTorrentFindPropersCacheFirst(unittest.TestCase):
    def test_unrelated_cache_hits_do_not_skip_live_search(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("CacheFirst")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = [
            {"name": "Other.Show.S01E01.PROPER.720p", "url": "http://example/a", "time": int(time.time())},
        ]
        provider.search = mock.Mock(return_value=[])
        candidates = [
            _proper_candidate(
                "President Curtis",
                1,
                1,
                8,
                "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
            )
        ]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        self.assertEqual(results, [])
        provider.search.assert_called()
        self.assertIn("President Curtis S01E08 1080p PROPER|REPACK|REAL", _queries(provider))

    def test_consumes_cached_proper_that_matches_history_and_still_searches_live(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("CacheProperGrp")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = [
            {
                "name": "Show.S01E01.PROPER-GRP.720p.HDTV",
                "url": "http://example/proper-grp",
                "time": int(time.time()),
            },
        ]
        provider.search = mock.Mock(return_value=[])
        candidates = [_proper_candidate("Show", 1, 1, 1, "Show.S01E01.720p.HDTV")]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Show.S01E01.PROPER-GRP.720p.HDTV")
        self.assertEqual(results[0].url, "http://example/proper-grp")
        provider.search.assert_called()
        provider.cache.list_propers.assert_called_once()

    def test_skips_live_when_rate_limited(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("RateLimited")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(return_value=[{"title": "should-not-call", "link": "http://x"}])
        provider._rate_limited_until = time.time() + 60
        candidates = [_proper_candidate("Show", 1, 1, 1, "Show.S01E01.720p.HDTV")]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        self.assertEqual(results, [])
        provider.search.assert_not_called()

    def test_shared_remainder_searches_season_pack_then_each_episode(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("SeasonCombine")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(return_value=[])

        show = mock.Mock()
        show.indexerid = 42
        show.name = "The Walking Dead: Daryl Dixon"
        show.air_by_date = False
        show.sports = False
        show.anime = False
        show.is_anime = False

        candidates = []
        for ep_no in (1, 2, 3, 4):
            episode = mock.Mock()
            episode.show = show
            episode.season = 3
            episode.scene_season = 3
            episode.episode = ep_no
            episode.scene_episode = ep_no
            resource = f"The.Walking.Dead.Daryl.Dixon.S03E{ep_no:02d}.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"
            candidates.append((show, episode, resource))

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            provider.find_propers(search_date=sc_now())

        queries = _queries(provider)
        self.assertEqual(provider.search.call_count, 5)
        self.assertIn("The Walking Dead: Daryl Dixon S03 1080p PROPER|REPACK|REAL", queries)
        self.assertIn("The Walking Dead: Daryl Dixon S03E01 1080p PROPER|REPACK|REAL", queries)
        self.assertIn("The Walking Dead: Daryl Dixon S03E04 1080p PROPER|REPACK|REAL", queries)

    def test_mixed_remainders_stay_per_episode(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("TwoSeasons")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(return_value=[])

        show = mock.Mock()
        show.indexerid = 42
        show.name = "Daryl Dixon"
        show.air_by_date = False
        show.sports = False
        show.anime = False
        show.is_anime = False

        resources = {
            (2, 1): "Daryl.Dixon.S02E01.1080p.WEBRip.x265-PSA",
            (3, 1): "Daryl.Dixon.S03E01.1080p.WEBRip.x265-PSA",
            (3, 2): "Daryl.Dixon.S03E02.720p.HDTV.x264-NTb",
        }
        candidates = []
        for season, ep_no in ((2, 1), (3, 1), (3, 2)):
            episode = mock.Mock()
            episode.show = show
            episode.season = season
            episode.scene_season = season
            episode.episode = ep_no
            episode.scene_episode = ep_no
            candidates.append((show, episode, resources[(season, ep_no)]))

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            provider.find_propers(search_date=sc_now())

        queries = _queries(provider)
        self.assertEqual(provider.search.call_count, 3)
        self.assertTrue(any("S02E01" in query for query in queries))
        self.assertTrue(any("S03E01" in query for query in queries))
        self.assertTrue(any("S03E02" in query for query in queries))
        self.assertFalse(any(re.search(r"\bS03\b", query) and "E0" not in query for query in queries))

    def test_anime_episodes_are_searched_individually(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("AnimeCombine")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(return_value=[])

        show = mock.Mock()
        show.indexerid = 99
        show.name = "Naruto"
        show.air_by_date = False
        show.sports = False
        show.anime = 1
        show.is_anime = True

        candidates = []
        for season, ep_no, absolute in ((1, 1, 1), (2, 5, 5)):
            episode = mock.Mock()
            episode.show = show
            episode.season = season
            episode.scene_season = season
            episode.episode = ep_no
            episode.scene_episode = ep_no
            episode.scene_absolute_number = absolute
            resource = f"Naruto.S{season:02d}E{ep_no:02d}.1080p.WEBRip.x265-SubsPlease"
            candidates.append((show, episode, resource))

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            provider.find_propers(search_date=sc_now())

        queries = _queries(provider)
        self.assertEqual(provider.search.call_count, 2)
        self.assertTrue(any(query.startswith(("Naruto 001 ", "Naruto 01 ")) for query in queries))
        self.assertTrue(any(query.startswith(("Naruto 005 ", "Naruto 05 ")) for query in queries))
        self.assertTrue(all("1080p PROPER|REPACK|REAL" in query for query in queries))

    def test_stops_live_groups_after_429(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("StopAfter429")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []

        def search_and_limit(_strings):
            provider._rate_limited_until = time.time() + 60
            return []

        provider.search = mock.Mock(side_effect=search_and_limit)
        candidates = [
            _proper_candidate("Show A", 1, 1, 1, "Show.A.S01E01.720p.HDTV"),
            _proper_candidate("Show B", 2, 1, 1, "Show.B.S01E01.720p.HDTV"),
        ]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            provider.find_propers(search_date=sc_now())

        self.assertEqual(provider.search.call_count, 1)

    def test_live_propers_skip_titles_for_a_different_show(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("PierreFilter")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(
            return_value=[
                {"title": "Pierre S01E01 PROPER 1080p HEVC x265-MeGusta", "link": "http://example/pierre"},
                {"title": "Saint-Pierre S01E08 REPACK 1080p HEVC x265-MeGusta", "link": "http://example/saint"},
            ]
        )
        candidates = [_proper_candidate("Pierre", 1, 1, 1, "Pierre.S01E01.1080p.HEVC.x265-MeGusta")]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        names = [result.name for result in results]
        self.assertEqual(len(names), 1)
        self.assertTrue(names[0].startswith("Pierre."))
        self.assertFalse(any("Saint" in name for name in names))

    def test_president_curtis_keeps_matching_quality_and_remainder(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("PresidentCurtis")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(
            return_value=[
                {"title": "President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA", "link": "http://example/match"},
                {"title": "President.Curtis.S01E08.PROPER.720p.10bit.WEBRip.6CH.x265.HEVC-PSA", "link": "http://example/720"},
                {"title": "President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-NTb", "link": "http://example/ntb"},
            ]
        )
        candidates = [
            _proper_candidate(
                "President Curtis",
                1,
                1,
                8,
                "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
            )
        ]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        names = [result.name for result in results]
        self.assertEqual(names, ["President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"])
        self.assertEqual(_queries(provider), ["President Curtis S01E08 1080p PROPER|REPACK|REAL"])

    def test_president_curtis_720p_history_keeps_720p_proper(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("PresidentCurtis720")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(
            return_value=[
                {"title": "President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA", "link": "http://example/1080"},
                {"title": "President.Curtis.S01E08.PROPER.720p.10bit.WEBRip.6CH.x265.HEVC-PSA", "link": "http://example/720"},
            ]
        )
        candidates = [
            _proper_candidate(
                "President Curtis",
                1,
                1,
                8,
                "President.Curtis.S01E08.720p.10bit.WEBRip.6CH.x265.HEVC-PSA",
            )
        ]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        names = [result.name for result in results]
        self.assertEqual(names, ["President.Curtis.S01E08.PROPER.720p.10bit.WEBRip.6CH.x265.HEVC-PSA"])
        self.assertEqual(_queries(provider), ["President Curtis S01E08 720p PROPER|REPACK|REAL"])

    def test_season_pack_kept_when_remainder_matches(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("SeasonPackKeep")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = []
        provider.search = mock.Mock(
            return_value=[
                {"title": "President.Curtis.S01.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA", "link": "http://example/pack"},
            ]
        )
        show, ep1, resource = _proper_candidate(
            "President Curtis",
            1,
            1,
            7,
            "President.Curtis.S01E07.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
        )
        ep2 = mock.Mock()
        ep2.show = show
        ep2.season = 1
        ep2.scene_season = 1
        ep2.episode = 8
        ep2.scene_episode = 8
        candidates = [
            (show, ep1, resource),
            (show, ep2, "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"),
        ]

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter(candidates)):
            results = provider.find_propers(search_date=sc_now())

        names = [result.name for result in results]
        self.assertEqual(names, ["President.Curtis.S01.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"])
        queries = _queries(provider)
        self.assertEqual(queries[0], "President Curtis S01 1080p PROPER|REPACK|REAL")
        self.assertIn("President Curtis S01E07 1080p PROPER|REPACK|REAL", queries)
        self.assertIn("President Curtis S01E08 1080p PROPER|REPACK|REAL", queries)


class TestProperFinderFingerprint(unittest.TestCase):
    def test_fingerprint_matching_history_requires_quality_and_remainder(self):
        finder = ProperFinder()
        proper = mock.Mock()
        proper.indexerid = 1
        proper.season = 1
        proper.episode = 8
        proper.quality = 8
        proper.name = "President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"
        proper.show.is_anime = False
        latest = {(1, 8): "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"}

        with mock.patch.object(finder, "_latest_history_resources", return_value=latest):
            matched = finder._fingerprint_matching_history(proper, False, sc_now())
        self.assertEqual(list(matched), [(1, 8)])

        proper.name = "President.Curtis.S01E08.PROPER.720p.10bit.WEBRip.6CH.x265.HEVC-PSA"
        with mock.patch.object(finder, "_latest_history_resources", return_value=latest):
            self.assertEqual(finder._fingerprint_matching_history(proper, False, sc_now()), {})

        proper.name = "President.Curtis.S01E08.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-NTb"
        with mock.patch.object(finder, "_latest_history_resources", return_value=latest):
            self.assertEqual(finder._fingerprint_matching_history(proper, False, sc_now()), {})

    def test_season_pack_matches_shared_remainder_history(self):
        finder = ProperFinder()
        proper = mock.Mock()
        proper.indexerid = 1
        proper.season = 1
        proper.episode = -1
        proper.quality = 8
        proper.name = "President.Curtis.S01.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"
        proper.show.is_anime = False
        latest = {
            (1, 7): "President.Curtis.S01E07.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
            (1, 8): "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
        }

        with mock.patch.object(finder, "_latest_history_resources", return_value=latest):
            matched = finder._fingerprint_matching_history(proper, True, sc_now())
        self.assertEqual(set(matched), {(1, 7), (1, 8)})

    def test_download_propers_snatches_matching_season_pack_episodes(self):
        finder = ProperFinder()
        show = mock.Mock()
        show.is_anime = False
        ep7 = mock.Mock()
        ep8 = mock.Mock()
        show.get_episode.side_effect = lambda season, episode: {7: ep7, 8: ep8}[episode]
        provider = mock.Mock()
        result = mock.Mock()
        provider.get_result.return_value = result
        proper = mock.Mock()
        proper.indexerid = 1
        proper.season = 1
        proper.episode = -1
        proper.quality = 8
        proper.name = "President.Curtis.S01.PROPER.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA"
        proper.url = "http://example/pack"
        proper.show = show
        proper.provider = provider
        proper.release_group = "PSA"
        proper.version = -1
        proper.content = None
        latest = {
            (1, 7): "President.Curtis.S01E07.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
            (1, 8): "President.Curtis.S01E08.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA",
        }

        with mock.patch.object(finder, "_latest_history_resources", return_value=latest):
            with mock.patch("sickchill.oldbeard.properFinder.snatch_episode") as snatch:
                with mock.patch("sickchill.oldbeard.properFinder.time.sleep"):
                    with mock.patch("sickchill.oldbeard.properFinder.cpu_presets", {None: 0}):
                        finder._download_propers([proper])

        provider.get_result.assert_called_once()
        episodes = provider.get_result.call_args[0][0]
        self.assertEqual(episodes, [ep7, ep8])
        snatch.assert_called_once()


class TestProviderRateLimit(unittest.TestCase):
    def test_get_url_skips_while_rate_limited(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("Limited")
        provider._rate_limited_until = time.time() + 60
        with mock.patch("sickchill.providers.GenericProvider.getURL") as get_url:
            self.assertEqual(provider.get_url("http://example/search"), "")
            get_url.assert_not_called()

    def test_429_hook_marks_without_sleep(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("Hook429")
        response = mock.Mock()
        response.status_code = 429
        response.request.method = "GET"
        response.request.url = "http://example/search"
        response.headers = {"Retry-After": "20"}

        with mock.patch("sickchill.providers.GenericProvider.time.sleep") as slept:
            provider.get_url_hook(response)
            slept.assert_not_called()
            provider.get_url_hook(response)
            slept.assert_not_called()
        self.assertTrue(provider.is_rate_limited())

    def test_download_result_skips_when_rate_limited(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("DlLimited")
        provider._rate_limited_until = time.time() + 60
        provider.login = mock.Mock(return_value=True)
        self.assertFalse(provider.download_result(mock.Mock()))
        provider.login.assert_not_called()

    def test_download_result_stops_after_429_in_loop(self):
        from sickchill.providers.GenericProvider import GenericProvider

        provider = GenericProvider("DlStop")
        provider.login = mock.Mock(return_value=True)
        provider._make_url = mock.Mock(return_value=(["http://example/a", "http://example/b"], "/tmp/x.torrent"))
        provider._verify_download = mock.Mock(return_value=False)

        def download_then_limit(*_args, **_kwargs):
            provider._rate_limited_until = time.time() + 60

        with mock.patch("sickchill.providers.GenericProvider.download_file", side_effect=download_then_limit) as downloaded:
            self.assertFalse(provider.download_result(mock.Mock()))
            self.assertEqual(downloaded.call_count, 1)


class TestGenericFindPropersCachedProperGrp(conftest.SickChillTestDBCase):
    def setUp(self):
        super().setUp()
        from sickchill.providers.GenericProvider import GenericProvider

        self.cache_db = db.DBConnection("cache.db")
        self.provider = GenericProvider("GenericProperGrp")
        self.provider_id = self.provider.get_id()
        self.provider.cache = TVCache(self.provider)
        self.cache_db.action("DELETE FROM results WHERE provider = ?", [self.provider_id])

    def tearDown(self):
        self.cache_db.action("DELETE FROM results WHERE provider = ?", [self.provider_id])
        super().tearDown()

    def test_generic_find_propers_consumes_cached_proper_grp(self):
        name = "Show.S01E01.PROPER-GRP.720p.HDTV"
        ts = int(time.time())
        self.cache_db.action(
            "INSERT OR IGNORE INTO results (provider, name, season, episodes, indexerid, url, time, quality, release_group, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [self.provider_id, name, 1, "|1|", 12345, f"http://example/{self.provider_id}/{name}", ts, "HD", "", -1],
        )

        results = self.provider.find_propers(search_date=None)
        names = [r.name for r in results]
        self.assertIn(name, names)


class TestProperQueueAndInterval(unittest.TestCase):
    def test_run_enqueues_instead_of_searching(self):
        from sickchill import settings
        from sickchill.oldbeard.search_queue import ProperSearchQueueItem, SearchQueue

        finder = ProperFinder()
        queue = SearchQueue()
        settings.searchQueueScheduler = mock.Mock()
        settings.searchQueueScheduler.action = queue

        finder.run(force=True)
        self.assertTrue(queue.is_proper_search_in_progress())
        self.assertIsInstance(queue.queue[0], ProperSearchQueueItem)

    def test_change_check_propers_interval_updates_cycle(self):
        from sickchill import settings
        from sickchill.oldbeard import config, scheduler

        settings.properFinderScheduler = scheduler.Scheduler(lambda: None)
        config.change_check_propers_interval("90m")
        self.assertEqual(settings.CHECK_PROPERS_INTERVAL, "90m")
        self.assertEqual(settings.properFinderScheduler.cycleTime, datetime.timedelta(minutes=90))

    def test_change_download_propers_window_days(self):
        from sickchill import settings
        from sickchill.oldbeard import config

        previous = settings.DOWNLOAD_PROPERS_WINDOW_DAYS
        try:
            config.change_download_propers_window_days(5)
            self.assertEqual(settings.DOWNLOAD_PROPERS_WINDOW_DAYS, 5)
            config.change_download_propers_window_days(99)
            self.assertEqual(settings.DOWNLOAD_PROPERS_WINDOW_DAYS, 2)
            config.change_download_propers_window_days(0)
            self.assertEqual(settings.DOWNLOAD_PROPERS_WINDOW_DAYS, 2)
        finally:
            settings.DOWNLOAD_PROPERS_WINDOW_DAYS = previous

    def test_proper_search_date_respects_setting(self):
        from sickchill import settings

        finder = ProperFinder()
        previous = settings.DOWNLOAD_PROPERS_WINDOW_DAYS
        try:
            settings.DOWNLOAD_PROPERS_WINDOW_DAYS = 5
            with mock.patch.object(finder, "_get_last_proper_search", return_value=datetime.date.min):
                with mock.patch("sickchill.oldbeard.properFinder.sc_now") as now_mock:
                    fixed = datetime.datetime(2026, 9, 4, 15, 0, 0, tzinfo=sc_timezone)
                    now_mock.return_value = fixed
                    got = finder._proper_search_date()
            self.assertEqual(got, fixed - datetime.timedelta(days=5))
        finally:
            settings.DOWNLOAD_PROPERS_WINDOW_DAYS = previous


if __name__ == "__main__":
    unittest.main()
