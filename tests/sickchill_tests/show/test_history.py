"""
Test history
"""

import unittest

from sickchill.oldbeard.common import Quality
from sickchill.show.History import History


class HistoryTests(unittest.TestCase):
    """
    Test history
    """

    def test_get_actions(self):
        """
        Tests whether or not the different kinds of actions an episode can have are returned correctly
        """
        test_cases = {
            None: [],
            "": [],
            "wrong": [],
            "downloaded": Quality.DOWNLOADED,
            "Downloaded": Quality.DOWNLOADED,
            "snatched": Quality.SNATCHED,
            "Snatched": Quality.SNATCHED,
        }

        unicode_test_cases = {
            "": [],
            "wrong": [],
            "downloaded": Quality.DOWNLOADED,
            "Downloaded": Quality.DOWNLOADED,
            "snatched": Quality.SNATCHED,
            "Snatched": Quality.SNATCHED,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in tests.items():
                assert History._get_actions(action) == result

    def test_get_limit(self):
        """
        Tests the static get limit method which should return the limit on the amount of elements that should be shown/returned
        """
        test_cases = {
            None: 0,
            "": 0,
            "0": 0,
            "5": 5,
            "-5": 0,
            "1.5": 0,
            "-1.5": 0,
            5: 5,
            -5: 0,
            1.5: 1,
            -1.5: 0,
        }

        unicode_test_cases = {
            "": 0,
            "0": 0,
            "5": 5,
            "-5": 0,
            "1.5": 0,
            "-1.5": 0,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in tests.items():
                assert History._get_limit(action) == result


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
