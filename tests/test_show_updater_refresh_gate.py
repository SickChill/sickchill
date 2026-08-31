"""Tests for ShowUpdater disk-refresh gating (mtime + interval)."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import show_dir_mtime


def _show(indexer_id=1, location="/shows/Test"):
    show = MagicMock()
    show.indexerid = indexer_id
    show.name = "Test"
    show._location = location
    return show


class TestNewestDirMtime(unittest.TestCase):
    def test_nested_season_dir_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            season = root / "Season 01"
            season.mkdir()
            # Make season dir clearly newer than root
            root_mtime = os.path.getmtime(root)
            newer = root_mtime + 100
            os.utime(season, (newer, newer))
            # Keep root older
            os.utime(root, (root_mtime, root_mtime))

            result = show_dir_mtime.newest_dir_mtime(str(root))
            self.assertIsNotNone(result)
            self.assertGreaterEqual(result, newer - 1)
            self.assertGreater(result, os.path.getmtime(root))

    def test_returns_none_for_missing(self):
        self.assertIsNone(show_dir_mtime.newest_dir_mtime("/no/such/show/dir/xyz"))


class TestNeedsDiskRefresh(unittest.TestCase):
    def test_interval_minus_one_never(self):
        show = _show()
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch.object(show_dir_mtime, "get_cached_row", return_value=None):
                needs, reason = show_dir_mtime.needs_disk_refresh(show, -1)
        self.assertFalse(needs)
        self.assertIn("disabled", reason)

    def test_no_cache_row_seeds_refresh(self):
        show = _show()
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=None):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertTrue(needs)
        self.assertIn("seed", reason)

    def test_mtime_changed(self):
        show = _show()
        row = {"indexer_id": 1, "location": "/shows/Test", "mtime": 100.0, "last_disk_refresh": int(time.time())}
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=200.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=row):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertTrue(needs)
        self.assertIn("mtime changed", reason)

    def test_location_changed(self):
        show = _show()
        show._location = "/shows/New"
        row = {"indexer_id": 1, "location": "/shows/Old", "mtime": 100.0, "last_disk_refresh": int(time.time())}
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=row):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertTrue(needs)
        self.assertIn("location changed", reason)

    def test_mtime_unchanged_recent_refresh_skips(self):
        show = _show()
        row = {
            "indexer_id": 1,
            "location": "/shows/Test",
            "mtime": 100.0,
            "last_disk_refresh": int(time.time()) - 86400,  # 1 day ago
        }
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=row):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertFalse(needs)
        self.assertIn("mtime unchanged", reason)

    def test_mtime_unchanged_stale_refresh_runs(self):
        show = _show()
        row = {
            "indexer_id": 1,
            "location": "/shows/Test",
            "mtime": 100.0,
            "last_disk_refresh": int(time.time()) - (8 * 86400),
        }
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=row):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertTrue(needs)
        self.assertIn("days ago", reason)

    def test_interval_zero_mtime_only_skips_when_equal(self):
        show = _show()
        row = {
            "indexer_id": 1,
            "location": "/shows/Test",
            "mtime": 100.0,
            "last_disk_refresh": int(time.time()) - (30 * 86400),
        }
        with patch.object(show_dir_mtime, "get_show_dir_mtime", return_value=100.0):
            with patch("os.path.isdir", return_value=True):
                with patch.object(show_dir_mtime, "get_cached_row", return_value=row):
                    needs, reason = show_dir_mtime.needs_disk_refresh(show, 0)
        self.assertFalse(needs)
        self.assertIn("mtime-only", reason)

    def test_missing_folder_skips(self):
        show = _show()
        with patch("os.path.isdir", return_value=False):
            needs, reason = show_dir_mtime.needs_disk_refresh(show, 7)
        self.assertFalse(needs)
        self.assertIn("missing", reason)


class TestShowUpdaterScheduling(unittest.TestCase):
    """Light integration of ShowUpdater decision branches with mocks."""

    @patch("sickchill.show_updater.ui")
    @patch("sickchill.show_updater.network_timezones")
    @patch("sickchill.show_updater.db")
    @patch("sickchill.show_updater.sickchill")
    def test_in_feed_queues_update_not_refresh_only(self, mock_sc, mock_db, mock_tz, mock_ui):
        from sickchill import settings
        from sickchill.show_updater import ShowUpdater

        show_in = MagicMock()
        show_in.indexerid = 111
        show_in.name = "In Feed"
        show_in.status = "Continuing"
        show_in.paused = False
        show_in.last_update_indexer = 1
        show_in.idxr.clear_episode_cache = MagicMock()
        show_in.update = MagicMock(return_value="update-item")
        show_in.refresh = MagicMock(return_value="refresh-item")
        show_in.next_episode = MagicMock()

        show_out = MagicMock()
        show_out.indexerid = 222
        show_out.name = "Out Feed"
        show_out.status = "Continuing"
        show_out.paused = False
        show_out.last_update_indexer = 1
        show_out.update = MagicMock(return_value="update-item")
        show_out.refresh = MagicMock(return_value="refresh-item")
        show_out.next_episode = MagicMock()

        settings.show_list = [show_in, show_out]
        settings.ENDED_SHOWS_UPDATE_INTERVAL = 14
        settings.SHOW_DISK_REFRESH_DAYS = 7
        settings.stopping = False
        settings.restarting = False

        provider = MagicMock()
        provider.name = "theTVDB"

        class Feed:
            feed_ok = True

            def series(self):
                # Real TVDB shim replaces .series method with the result list after the call
                result = [{"id": 111}]
                self.series = result
                return result

        indexer_api = MagicMock()
        indexer_api.updates.return_value = Feed()

        class IndexerMap:
            def __iter__(self):
                return iter([(1, provider)])

            def __getitem__(self, key):
                return indexer_api

        mock_sc.indexer = IndexerMap()

        cache_con = MagicMock()
        # Row must support numeric index like sqlite3.Row: database_result[0][0]
        cache_con.select.return_value = [[str(int(time.time()) - 86400)]]
        mock_db.DBConnection.return_value = cache_con

        with patch("sickchill.show_updater.needs_disk_refresh", return_value=(False, "mtime unchanged")):
            ShowUpdater().run()

        show_in.update.assert_called_once()
        show_in.refresh.assert_not_called()
        show_out.update.assert_not_called()
        show_out.refresh.assert_not_called()

    @patch("sickchill.show_updater.ui")
    @patch("sickchill.show_updater.network_timezones")
    @patch("sickchill.show_updater.db")
    @patch("sickchill.show_updater.sickchill")
    def test_force_bypasses_disk_refresh_gate(self, mock_sc, mock_db, mock_tz, mock_ui):
        from sickchill import settings
        from sickchill.show_updater import ShowUpdater

        show_out = MagicMock()
        show_out.indexerid = 222
        show_out.name = "Out Feed"
        show_out.status = "Continuing"
        show_out.paused = False
        show_out.last_update_indexer = 1
        show_out.update = MagicMock(return_value="update-item")
        show_out.refresh = MagicMock(return_value="refresh-item")
        show_out.next_episode = MagicMock()

        settings.show_list = [show_out]
        settings.ENDED_SHOWS_UPDATE_INTERVAL = 14
        settings.SHOW_DISK_REFRESH_DAYS = 7
        settings.stopping = False
        settings.restarting = False

        provider = MagicMock()
        provider.name = "theTVDB"

        class Feed:
            feed_ok = True

            def series(self):
                result = []
                self.series = result
                return result

        indexer_api = MagicMock()
        indexer_api.updates.return_value = Feed()

        class IndexerMap:
            def __iter__(self):
                return iter([(1, provider)])

            def __getitem__(self, key):
                return indexer_api

        mock_sc.indexer = IndexerMap()
        cache_con = MagicMock()
        cache_con.select.return_value = [[str(int(time.time()) - 86400)]]
        mock_db.DBConnection.return_value = cache_con

        with patch("sickchill.show_updater.needs_disk_refresh") as mock_gate:
            mock_gate.return_value = (False, "mtime unchanged")
            ShowUpdater().run(force=True)
            mock_gate.assert_not_called()

        show_out.update.assert_not_called()
        show_out.refresh.assert_called_once_with(force=True)


if __name__ == "__main__":
    unittest.main()
