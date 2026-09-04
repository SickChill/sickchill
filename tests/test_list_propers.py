"""Phase 1: list_propers SQL scopes to provider; proper search watermark."""

from __future__ import annotations

import datetime
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


class TestTorrentFindPropersCacheFirst(unittest.TestCase):
    def test_skips_live_when_cache_has_hits(self):
        from sickchill.providers.torrent.TorrentProvider import TorrentProvider

        provider = TorrentProvider("CacheFirst")
        provider.cache = mock.Mock()
        provider.cache.list_propers.return_value = [
            {"name": "Show.S01E01.PROPER.720p", "url": "http://example/a", "time": int(time.time())},
        ]
        provider.search = mock.Mock(return_value=[{"title": "should-not-call"}])
        provider._get_title_and_url = mock.Mock(return_value=("x", "y"))

        with mock.patch.object(TorrentProvider, "_recent_proper_candidates", return_value=iter([])):
            results = provider.find_propers(search_date=sc_now())

        self.assertEqual(len(results), 1)
        provider.search.assert_not_called()

    def test_consumes_cached_proper_grp_via_list_propers(self):
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

        results = provider.find_propers(search_date=sc_now())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Show.S01E01.PROPER-GRP.720p.HDTV")
        self.assertEqual(results[0].url, "http://example/proper-grp")
        provider.search.assert_not_called()
        provider.cache.list_propers.assert_called_once()


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
