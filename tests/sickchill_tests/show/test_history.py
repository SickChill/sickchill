"""
Test history
"""

import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard.common import DOWNLOADED, Quality
from sickchill.show.History import History


class HistoryTests(unittest.TestCase):
    """
    Test history
    """

    def test_log_download_writes_related_episodes_for_multi_ep(self):
        """Multi-ep PP must history-log E04, E05, and E06 — not only the root."""
        history = History()
        show = MagicMock()
        show.indexerid = 299994

        def make_ep(episode_number, quality):
            ep = MagicMock()
            ep.show = show
            ep.season = 1
            ep.episode = episode_number
            # Distinct statuses so we catch accidentally logging root.status for every ep.
            ep.status = Quality.compositeStatus(DOWNLOADED, quality)
            ep.related_episodes = []
            return ep

        root = make_ep(4, Quality.SDTV)
        related_a = make_ep(5, Quality.HDTV)
        related_b = make_ep(6, Quality.FULLHDTV)
        root.related_episodes = [related_a, related_b]
        expected = [
            (root.status, 4),
            (related_a.status, 5),
            (related_b.status, 6),
        ]

        with patch.object(history, "_log_history_item") as log_item:
            history.log_download(root, "/videos/Puffin.Rock.S01E04E05E06.mkv", Quality.HDTV, group="MEMENTO", version=-1)

        self.assertEqual(log_item.call_count, 3)
        # positional: action, showid, season, episode, quality, resource, ...
        for call_args, (expected_status, expected_episode) in zip(log_item.call_args_list, expected, strict=True):
            self.assertEqual(call_args.args[0], expected_status)
            self.assertEqual(call_args.args[2], 1)  # season
            self.assertEqual(call_args.args[3], expected_episode)
            self.assertEqual(call_args.args[5], "/videos/Puffin.Rock.S01E04E05E06.mkv")

    def _history_with_failed(self, *rows):
        """History whose failed_db is, for this test only, a real in-memory table with the production schema."""
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute('CREATE TABLE failed ("release" TEXT, size NUMERIC, provider TEXT);')
        connection.executemany('INSERT INTO failed ("release", size, provider) VALUES (?, ?, ?)', rows)

        # trim() in __init__ queries the history table, which only exists once a DB test case has run;
        # skip it so these tests do not depend on ordering.
        with patch.object(History, "trim"):
            history = History()

        # History is a singleton, so patch failed_db for this test only; otherwise the fake leaks into later tests.
        failed_db = MagicMock()
        failed_db.select_one.side_effect = lambda query, args=None: connection.execute(query, args or []).fetchone() or []
        patcher = patch.object(history, "failed_db", failed_db)
        patcher.start()
        self.addCleanup(patcher.stop)
        return history

    def test_has_failed_matches_release_name_regardless_of_size(self):
        """A failed release must be rejected even when the search result carries no size (-1), as cache results do."""
        history = self._history_with_failed(("Show_Name_S01E01_1080p_WEB_DL_H_264_GROUP", 1773724000, "nzbGeek"))

        self.assertTrue(history.has_failed("Show.Name.S01E01.1080p.WEB-DL.H.264-GROUP"))

    def test_has_failed_false_for_release_not_recorded(self):
        history = self._history_with_failed(("Show_Name_S01E01_1080p_WEB_DL_H_264_GROUP", 1773724000, "nzbGeek"))

        self.assertFalse(history.has_failed("Show.Name.S01E01.1080p.WEB.h264-OTHER"))


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
