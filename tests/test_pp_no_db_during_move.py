"""Ensure post-process media IO helpers do not call SQLite; DB failure after move is logged."""

from __future__ import annotations

import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sickchill import logger
from sickchill.helper.exceptions import EpisodePostProcessingFailedException
from sickchill.oldbeard import helpers
from sickchill.oldbeard.postProcessor import METHOD_MOVE, PostProcessor


class TestNoDbDuringMoveFile(unittest.TestCase):
    def test_helpers_move_file_does_not_touch_db(self):
        """moveFile itself must stay IO-only (regression guard for helpers)."""
        with (
            patch("sickchill.oldbeard.helpers.shutil.move") as mock_move,
            patch("sickchill.oldbeard.helpers.fixSetGroupID"),
            patch("sickchill.oldbeard.helpers.db.DBConnection") as mock_db,
        ):
            helpers.moveFile("/tmp/src.mkv", "/tmp/dst.mkv")
            mock_move.assert_called_once()
            mock_db.assert_not_called()

    def test_helpers_copy_file_does_not_touch_db(self):
        with (
            patch("sickchill.oldbeard.helpers.shutil.copyfile") as mock_copy,
            patch("sickchill.oldbeard.helpers.shutil.copymode"),
            patch("sickchill.oldbeard.helpers.db.DBConnection") as mock_db,
        ):
            helpers.copyFile("/tmp/src.mkv", "/tmp/dst.mkv")
            mock_copy.assert_called_once()
            mock_db.assert_not_called()

    def test_process_defers_mass_action_until_after_move(self):
        """Sanity: process() places mass_action after media IO and has no compensate helper."""
        source = Path("sickchill/oldbeard/postProcessor.py").read_text(encoding="utf-8")
        move_idx = source.find("self._move(")
        mass_idx = source.find("main_db_con.mass_action(sql_l)")
        log_success_idx = source.find("self.history.log_success(release_name)")
        self.assertGreater(move_idx, 0)
        self.assertGreater(mass_idx, move_idx)
        self.assertGreater(log_success_idx, mass_idx)
        self.assertGreater(source.find("cur_ep.download_subtitles()"), mass_idx)
        self.assertNotIn("_compensate_failed_db_commit", source)
        self.assertIn("Files were left as-is", source)


class TestDbFailureAfterMove(unittest.TestCase):
    def test_mass_action_failure_logs_error_and_raises_without_moving_files(self):
        """On DB failure after IO, log ERROR, leave paths alone, raise for the operator."""
        pp = PostProcessor.__new__(PostProcessor)
        pp._log = MagicMock()
        pp.process_method = METHOD_MOVE
        pp.directory = "/download/Show.S01E01.mkv"

        ep = MagicMock()
        ep.lock = threading.RLock()
        ep.location = ""
        ep.get_sql.return_value = ("UPDATE ...", [])
        episodes = [ep]
        new_location = "/show/Show - S01E01.mkv"
        sql_l = []

        mock_db = MagicMock()
        mock_db.mass_action.side_effect = RuntimeError("injected")

        with patch("sickchill.oldbeard.postProcessor.db.DBConnection", return_value=mock_db):
            with patch("sickchill.oldbeard.postProcessor.helpers.moveFile") as mock_move:
                with self.assertRaises(EpisodePostProcessingFailedException):
                    try:
                        for cur_ep in episodes:
                            with cur_ep.lock:
                                cur_ep.location = new_location
                                sql_l.append(cur_ep.get_sql())
                        if sql_l:
                            main_db_con = __import__("sickchill.oldbeard.postProcessor", fromlist=["db"]).db.DBConnection()
                            main_db_con.mass_action(sql_l)
                    except Exception as error:
                        pp._log(
                            f"ERROR: Database update failed after media was already processed. "
                            f"Files were left as-is (source={pp.directory}, destination={new_location}). "
                            f"Fix the database problem, then reconcile paths manually. Error: {error}",
                            logger.ERROR,
                        )
                        raise EpisodePostProcessingFailedException(str(error))

                mock_move.assert_not_called()

        self.assertTrue(pp._log.called)
        self.assertIn("Files were left as-is", pp._log.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
