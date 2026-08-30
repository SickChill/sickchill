"""Ensure post-process media IO helpers do not call SQLite."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from sickchill.oldbeard import helpers


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
        """Sanity: process() source still documents / places mass_action after media IO."""
        from pathlib import Path

        source = Path("sickchill/oldbeard/postProcessor.py").read_text(encoding="utf-8")
        move_idx = source.find("self._move(")
        mass_idx = source.find("main_db_con.mass_action(sql_l)")
        log_success_idx = source.find("self.history.log_success(release_name)")
        self.assertGreater(move_idx, 0)
        self.assertGreater(mass_idx, move_idx)
        self.assertGreater(log_success_idx, mass_idx)
        # Subtitles after mass_action, not under the same pre-move get_sql block
        self.assertGreater(source.find("cur_ep.download_subtitles()"), mass_idx)
        self.assertNotIn("sql_l.append(cur_ep.get_sql())\n\n        # Just want to keep", source)


if __name__ == "__main__":
    unittest.main()
