"""Ensure post-process media IO stays ahead of DB writes; get_sql shape is mass_action-safe."""

from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        """Sanity: process() places mass_action after media IO."""
        source = Path("sickchill/oldbeard/postProcessor.py").read_text(encoding="utf-8")
        move_idx = source.find("self._move(")
        mass_idx = source.find("main_db_con.mass_action(sql_l)")
        self.assertGreater(move_idx, 0)
        self.assertGreater(mass_idx, move_idx)
        self.assertIn("sql_l.extend(sql)", source)
        self.assertIn("Files were left as-is", source)


class TestProcessMoveThenMassAction(unittest.TestCase):
    """Exercise PostProcessor.process() with production get_sql / mass_action shapes."""

    @staticmethod
    def _production_get_sql():
        # Matches TVEpisode.get_sql(): a one-element list containing the query tuple
        return [("UPDATE tv_episodes SET location = ? WHERE episode_id = ?", ["/show/ep.mkv", 1])]

    def test_process_move_before_mass_action_and_sql_shape(self):
        """
        Invoke production process() on a MOVE: media IO must run before mass_action,
        and mass_action must receive flat [("UPDATE ...", [...])] units (not nested lists).
        """
        call_order = []

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "Show.S01E01.mkv"
            show_dir = Path(tmp) / "Show Name"
            show_dir.mkdir()
            src.write_bytes(b"video")

            show = MagicMock()
            show.name = "Show Name"
            show.location = str(show_dir)
            show.get_location = str(show_dir)
            show.indexerid = 1
            show.indexer = 1
            show.quality = 500
            show.subtitles = False
            show.is_anime = False
            show.air_by_date = False
            show.sports = False
            show.season_folders = True

            ep = MagicMock()
            ep.lock = threading.RLock()
            ep.location = ""
            ep.season = 1
            ep.episode = 1
            ep.status = 0
            ep.related_episodes = []
            ep.pretty_name = "Show Name - S01E01"
            ep.show = show
            ep.proper_path.return_value = "Season 01/Show Name - S01E01"
            ep.get_sql.side_effect = lambda: self._production_get_sql()
            ep.cleanup_download_properties = MagicMock()
            ep.refresh_subtitles = MagicMock()
            ep.download_subtitles = MagicMock()
            ep.airdate_modify_stamp = MagicMock()
            ep.create_meta_files = MagicMock()

            def tracking_move(*args, **kwargs):
                call_order.append("move")

            def tracking_mass_action(query_list=None, **kwargs):
                call_order.append("mass_action")
                # Detect nesting defect: each unit must be (stmt, params), not [(stmt, params)]
                self.assertIsInstance(query_list, list)
                self.assertGreaterEqual(len(query_list), 1)
                for qu in query_list:
                    self.assertIsInstance(qu, (list, tuple))
                    self.assertEqual(len(qu), 2, f"expected [stmt, params] or (stmt, params), got nested {qu!r}")
                    self.assertIsInstance(qu[0], str)
                    self.assertTrue(qu[0].lstrip().upper().startswith("UPDATE"))
                    self.assertIsInstance(qu[1], list)
                raise RuntimeError("injected mass_action failure")

            mock_db = MagicMock()
            mock_db.mass_action.side_effect = tracking_mass_action
            mock_db.select.return_value = [{"last_season": 1}]

            pp = PostProcessor(str(src), process_method=METHOD_MOVE)
            pp._log = MagicMock()
            pp.history = MagicMock()
            pp.in_history = False
            pp.is_proper = False
            pp.release_group = ""
            pp.release_name = "Show.S01E01"

            with (
                patch.object(pp, "_find_info", return_value=(show, 1, [1], None, -1)),
                patch.object(pp, "_get_ep_obj", return_value=ep),
                patch.object(pp, "_get_quality", return_value=1),
                patch.object(pp, "_is_priority", return_value=True),
                patch.object(pp, "_checkForExistingFile", return_value=PostProcessor.DOESNT_EXIST),
                patch.object(pp, "_delete"),
                patch.object(pp, "_move", side_effect=tracking_move),
                patch("sickchill.oldbeard.postProcessor.db.DBConnection", return_value=mock_db),
                patch("sickchill.oldbeard.postProcessor.helpers.make_dirs", return_value=True),
                patch("sickchill.oldbeard.postProcessor.helpers.delete_empty_folders"),
                patch("sickchill.oldbeard.postProcessor.show_name_helpers.determine_release_name", return_value=None),
                patch("sickchill.oldbeard.postProcessor.settings.USE_FREE_SPACE_CHECK", False),
                patch("sickchill.oldbeard.postProcessor.settings.RENAME_EPISODES", True),
                patch("sickchill.oldbeard.postProcessor.settings.CREATE_MISSING_SHOW_DIRS", False),
                patch("sickchill.oldbeard.postProcessor.settings.USE_SUBTITLES", False),
                patch("sickchill.oldbeard.postProcessor.settings.MOVE_ASSOCIATED_FILES", False),
            ):
                with self.assertRaises(EpisodePostProcessingFailedException):
                    pp.process()

            self.assertEqual(call_order, ["move", "mass_action"])
            self.assertTrue(any("Files were left as-is" in str(c) for c in pp._log.call_args_list))
            # get_sql production shape used
            ep.get_sql.assert_called()


if __name__ == "__main__":
    unittest.main()
