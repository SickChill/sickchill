"""Tests for QueueEfficiency: USER priority, front=True, TBA/subtitle queue helpers."""

from __future__ import annotations

import datetime
import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import generic_queue, search_queue, show_queue
from sickchill.oldbeard.generic_queue import QueuePriorities


class TestQueuePrioritiesUser(unittest.TestCase):
    def test_user_priority_above_high(self):
        self.assertGreater(QueuePriorities.USER, QueuePriorities.HIGH)
        self.assertLess(QueuePriorities.USER, QueuePriorities.HIGH**2)

    def test_add_item_front_bumps_priority_and_added(self):
        q = generic_queue.GenericQueue()
        first = generic_queue.QueueItem("first")
        first.priority = QueuePriorities.HIGH
        q.add_item(first, front=True)

        second = generic_queue.QueueItem("second")
        second.priority = QueuePriorities.HIGH
        q.add_item(second, front=True)

        self.assertEqual(first.priority, QueuePriorities.USER)
        self.assertEqual(second.priority, QueuePriorities.USER)
        # Last click runs first among USER items
        self.assertLess(second.added, first.added)

    def test_front_does_not_outrank_remove(self):
        remove_priority = QueuePriorities.HIGH**2
        user_item = generic_queue.QueueItem("user")
        user_item.priority = QueuePriorities.HIGH
        q = generic_queue.GenericQueue()
        q.add_item(user_item, front=True)
        self.assertLess(user_item.priority, remove_priority)


class TestShowQueueTBA(unittest.TestCase):
    def test_tba_action_registered(self):
        self.assertIn(show_queue.ShowQueueActions.TBA_NAMES, show_queue.ShowQueueActions.names)

    def test_download_tba_names_rejects_while_updating(self):
        sq = show_queue.ShowQueue()
        show = MagicMock()
        show.name = "Test Show"
        show.indexerid = 1
        from sickchill.helper.exceptions import CantUpdateShowException

        with patch.object(sq, "is_being_updated", return_value=True):
            with self.assertRaises(CantUpdateShowException):
                sq.download_tba_names(show)

    def test_download_tba_names_promotes_queued_update(self):
        sq = show_queue.ShowQueue()
        show = MagicMock()
        show.name = "Test Show"
        show.indexerid = 99
        update_item = show_queue.QueueItemUpdate(show, force=False)
        update_item.priority = QueuePriorities.HIGH
        sq.add_item(update_item)  # scheduled HIGH, not front

        other = show_queue.QueueItemUpdate(MagicMock(name="Other", indexerid=1), force=False)
        other.priority = QueuePriorities.HIGH
        sq.add_item(other)

        promoted = sq.download_tba_names(show)
        self.assertIs(promoted, update_item)
        self.assertEqual(update_item.priority, QueuePriorities.USER)
        self.assertNotIn(show_queue.ShowQueueActions.TBA_NAMES, [x.action_id for x in sq.queue if x.show and x.show.indexerid == 99])


class TestShowQueuePromote(unittest.TestCase):
    def test_update_show_front_promotes_existing(self):
        sq = show_queue.ShowQueue()
        show = MagicMock()
        show.name = "Promoted Show"
        show.indexerid = 7
        existing = show_queue.QueueItemUpdate(show, force=False)
        existing.priority = QueuePriorities.HIGH
        sq.add_item(existing)

        result = sq.update_show(show, force=True, front=True)
        self.assertIs(result, existing)
        self.assertEqual(existing.priority, QueuePriorities.USER)
        self.assertEqual(len([x for x in sq.queue if x.show and x.show.indexerid == 7]), 1)

    def test_refresh_show_front_promotes_queued_update(self):
        sq = show_queue.ShowQueue()
        show = MagicMock()
        show.name = "Refresh Show"
        show.indexerid = 8
        show.paused = False
        existing = show_queue.QueueItemUpdate(show, force=False)
        existing.priority = QueuePriorities.HIGH
        sq.add_item(existing)

        result = sq.refresh_show(show, force=True, front=True)
        self.assertIs(result, existing)
        self.assertEqual(existing.priority, QueuePriorities.USER)


class TestSearchQueueSubtitles(unittest.TestCase):
    def test_subtitle_item_constants(self):
        self.assertEqual(search_queue.EPISODE_SUBTITLE_SEARCH, 50)

    def test_queue_head_kind_daily(self):
        sq = search_queue.SearchQueue()
        sq.currentItem = search_queue.DailySearchQueueItem()
        self.assertEqual(sq.queue_head_kind(), "daily")

    def test_is_ep_subtitle_in_queue(self):
        sq = search_queue.SearchQueue()
        show = MagicMock()
        show.indexerid = 42
        segment = MagicMock()
        segment.season = 1
        segment.episode = 2
        segment.pretty_name = "S01E02"
        item = search_queue.SubtitleEpisodeQueueItem(show, segment)
        sq.queue.append(item)
        self.assertTrue(sq.is_ep_subtitle_in_queue(segment))
        self.assertTrue(sq.is_ep_subtitle_in_queue(segment, force_lang=None))
        # Different language is not the same job
        self.assertFalse(sq.is_ep_subtitle_in_queue(segment, force_lang="en"))

    def test_add_subtitle_returns_running_item(self):
        sq = search_queue.SearchQueue()
        show = MagicMock()
        show.indexerid = 42
        segment = MagicMock()
        segment.season = 1
        segment.episode = 2
        running = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang=None)
        sq.currentItem = running
        duplicate = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang=None)
        result = sq.add_item(duplicate, front=True)
        self.assertIs(result, running)
        self.assertEqual(len(sq.queue), 0)

    def test_add_subtitle_different_lang_allowed(self):
        sq = search_queue.SearchQueue()
        show = MagicMock()
        show.indexerid = 42
        segment = MagicMock()
        segment.season = 1
        segment.episode = 2
        first = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang=None)
        sq.add_item(first, front=True)
        second = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang="en")
        result = sq.add_item(second, front=True)
        self.assertIs(result, second)
        self.assertEqual(len(sq.queue), 2)

    def test_empty_force_lang_dedupes_with_none(self):
        sq = search_queue.SearchQueue()
        show = MagicMock()
        show.indexerid = 42
        segment = MagicMock()
        segment.season = 1
        segment.episode = 2
        first = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang=None)
        self.assertIsNone(first.force_lang)
        sq.add_item(first, front=True)
        blank = search_queue.SubtitleEpisodeQueueItem(show, segment, force_lang="")
        self.assertIsNone(blank.force_lang)
        result = sq.add_item(blank, front=True)
        self.assertIs(result, first)
        self.assertEqual(len(sq.queue), 1)
        self.assertTrue(sq.is_ep_subtitle_in_queue(segment, force_lang="  "))

    def test_duplicate_subtitle_without_front_does_not_promote(self):
        sq = search_queue.SearchQueue()
        show = MagicMock()
        show.indexerid = 42
        segment = MagicMock()
        segment.season = 1
        segment.episode = 2
        first = search_queue.SubtitleEpisodeQueueItem(show, segment)
        first.priority = QueuePriorities.HIGH
        sq.add_item(first)  # no front
        original_priority = first.priority
        original_added = first.added
        duplicate = search_queue.SubtitleEpisodeQueueItem(show, segment)
        result = sq.add_item(duplicate, front=False)
        self.assertIs(result, first)
        self.assertEqual(first.priority, original_priority)
        self.assertEqual(first.added, original_added)

    def test_download_subtitles_returns_running_show_item(self):
        sq = show_queue.ShowQueue()
        show = MagicMock()
        show.name = "Sub Show"
        show.indexerid = 11
        running = show_queue.QueueItemSubtitle(show)
        sq.currentItem = running
        with patch.object(sq, "is_being_subtitled", return_value=True):
            result = sq.download_subtitles(show)
        self.assertIs(result, running)
        self.assertEqual(len(sq.queue), 0)


class TestSeasonTypesAllowFetch(unittest.TestCase):
    def test_allow_fetch_false_returns_defaults_on_miss(self):
        from sickchill.show.indexers.tvdb import TVDB

        idxr = MagicMock(spec=TVDB)
        # Bind real methods we care about
        idxr._season_types_mem_cache = {}
        idxr._series_cache_ttl = 0
        idxr._SEASON_TYPES_CACHE_VERSION = TVDB._SEASON_TYPES_CACHE_VERSION
        idxr._default_season_types = TVDB._default_season_types
        idxr._fetch_series_season_types = MagicMock(return_value=[{"slug": "netflix", "name": "Netflix"}])

        with patch("sickchill.oldbeard.db.DBConnection") as mock_db:
            mock_db.return_value.select.return_value = []
            result = TVDB.series_season_types(idxr, 12345, use_cache=True, allow_fetch=False)

        self.assertEqual(result, TVDB._default_season_types())
        idxr._fetch_series_season_types.assert_not_called()


if __name__ == "__main__":
    unittest.main()
