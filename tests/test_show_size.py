"""Stored tv_shows.show_size: schema 44.8, recalc, refresh, post-process batch."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import db
from sickchill.oldbeard.databases.main import TARGET_DB_MAJOR, TARGET_DB_MINOR, AddShowSize, ReconcileSchemaVersion, _full_schema_present
from sickchill.oldbeard.processTV import ProcessResult, _update_processed_show_sizes, process_media
from sickchill.oldbeard.show_queue import QueueItemRefresh
from sickchill.tv import TVShow
from tests import conftest


class TestShowSizeSchema(conftest.SickChillTestDBCase):
    def test_upgrade_has_show_size_and_version_44_8(self):
        con = db.DBConnection()
        self.assertTrue(con.has_column("tv_shows", "show_size"))
        self.assertTrue(_full_schema_present(con))
        self.assertEqual(con.version, (TARGET_DB_MAJOR, TARGET_DB_MINOR))
        self.assertEqual(con.version, (44, 8))

    def test_reconcile_sets_version_to_44_8_when_full_schema_present(self):
        con = db.DBConnection()
        con.action("UPDATE db_version SET db_minor_version = 4")
        self.assertTrue(_full_schema_present(con))
        ReconcileSchemaVersion(con).execute()
        self.assertEqual(con.version, (44, 8))

    def test_add_show_size_runs_when_column_exists_but_version_is_behind(self):
        con = db.DBConnection()
        con.action("UPDATE db_version SET db_minor_version = 7")
        migration = AddShowSize(con)
        self.assertTrue(con.has_column("tv_shows", "show_size"))
        self.assertFalse(migration.test())
        with patch("sickchill.oldbeard.databases.main.backup_database"):
            migration.execute()
        self.assertEqual(con.version, (44, 8))


class TestRecalculateShowSize(conftest.SickChillTestDBCase):
    def test_recalculate_show_size_sums_episode_file_sizes(self):
        show = TVShow(1, 4242, "en")
        show.name = "Size Show"
        show._location = "/tmp/size-show"
        show.save_to_db()

        con = db.DBConnection()
        con.action(
            "INSERT INTO tv_episodes (showid, indexerid, indexer, season, episode, status, location, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [4242, 1, 1, 1, 1, 1, "/tmp/a.mkv", 100],
        )
        con.action(
            "INSERT INTO tv_episodes (showid, indexerid, indexer, season, episode, status, location, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [4242, 2, 1, 1, 2, 1, "/tmp/b.mkv", 250],
        )

        show.recalculate_show_size()
        self.assertEqual(show.show_size, 350)

        row = con.select("SELECT show_size FROM tv_shows WHERE indexer_id = ?", [4242])
        self.assertEqual(int(row[0]["show_size"]), 350)

    def test_recalculate_show_size_counts_each_location_once(self):
        show = TVShow(1, 4243, "en")
        show.name = "Multi Ep Size Show"
        show._location = "/tmp/multi-size-show"
        show.save_to_db()

        con = db.DBConnection()
        shared = "/tmp/show.s01e01e02.mkv"
        con.action(
            "INSERT INTO tv_episodes (showid, indexerid, indexer, season, episode, status, location, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [4243, 1, 1, 1, 1, 1, shared, 100],
        )
        con.action(
            "INSERT INTO tv_episodes (showid, indexerid, indexer, season, episode, status, location, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [4243, 2, 1, 1, 2, 1, shared, 100],
        )
        con.action(
            "INSERT INTO tv_episodes (showid, indexerid, indexer, season, episode, status, location, file_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [4243, 3, 1, 1, 3, 1, "", 50],
        )

        show.recalculate_show_size()
        self.assertEqual(show.show_size, 100)

    def test_recalculate_show_size_zero_when_no_episodes(self):
        show = TVShow(1, 4343, "en")
        show.name = "Empty Size Show"
        show._location = "/tmp/empty-size-show"
        show.save_to_db()
        show.recalculate_show_size()
        self.assertEqual(show.show_size, 0)


class TestRefreshRecalculatesShowSize(unittest.TestCase):
    def test_queue_item_refresh_recalculates_show_size(self):
        show = MagicMock()
        item = QueueItemRefresh(show, force=False, silent=True)
        with (
            patch.object(item, "finish"),
            patch("sickchill.oldbeard.show_queue.scene_numbering.xem_refresh"),
            patch("sickchill.oldbeard.show_dir_mtime.stamp_show_dir_mtime"),
        ):
            item.run()
        show.refresh_dir.assert_called_once()
        show.recalculate_show_size.assert_called_once()


class TestPostProcessBatchShowSize(unittest.TestCase):
    def test_process_media_records_show_once_per_success(self):
        show = MagicMock()
        result = ProcessResult()
        processor = MagicMock()
        processor.process.return_value = True
        processor.show = show
        processor.log = ""
        processor.failure_reason = ""
        with (
            patch("sickchill.oldbeard.processTV.postProcessor.PostProcessor", return_value=processor),
            patch("sickchill.oldbeard.processTV.already_processed", return_value=False),
        ):
            process_media("/tmp", ["a.mkv", "b.mkv"], None, "copy", False, False, result)
        self.assertEqual(result.processed_shows, {show})
        self.assertEqual(processor.process.call_count, 2)

    def test_process_media_does_not_record_show_on_failure(self):
        show = MagicMock()
        result = ProcessResult()
        processor = MagicMock()
        processor.process.return_value = False
        processor.show = show
        processor.log = ""
        processor.failure_reason = "nope"
        with (
            patch("sickchill.oldbeard.processTV.postProcessor.PostProcessor", return_value=processor),
            patch("sickchill.oldbeard.processTV.already_processed", return_value=False),
        ):
            process_media("/tmp", ["a.mkv"], None, "copy", False, False, result)
        self.assertEqual(result.processed_shows, set())

    def test_update_processed_show_sizes_calls_recalculate_once_per_show(self):
        show_a = MagicMock()
        show_b = MagicMock()
        result = ProcessResult()
        result.processed_shows = {show_a, show_b}
        _update_processed_show_sizes(result)
        show_a.recalculate_show_size.assert_called_once()
        show_b.recalculate_show_size.assert_called_once()
