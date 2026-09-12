"""
Test history
"""

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

        def make_ep(episode_number):
            ep = MagicMock()
            ep.show = show
            ep.season = 1
            ep.episode = episode_number
            ep.status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            ep.related_episodes = []
            return ep

        root = make_ep(4)
        root.related_episodes = [make_ep(5), make_ep(6)]

        with patch.object(history, "_log_history_item") as log_item:
            history.log_download(root, "/videos/Puffin.Rock.S01E04E05E06.mkv", Quality.HDTV, group="MEMENTO", version=-1)

        self.assertEqual(log_item.call_count, 3)
        # positional: action, showid, season, episode, quality, resource, ...
        logged_episodes = [c.args[3] for c in log_item.call_args_list]
        self.assertEqual(logged_episodes, [4, 5, 6])
        for c in log_item.call_args_list:
            self.assertEqual(c.args[2], 1)  # season
            self.assertEqual(c.args[5], "/videos/Puffin.Rock.S01E04E05E06.mkv")


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
