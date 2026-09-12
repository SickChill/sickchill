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


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
