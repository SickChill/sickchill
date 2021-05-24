"""
Tests for SickChill show
"""

import unittest

from .test_coming_episodes import ComingEpisodesTests
from .test_history import HistoryTests
from .test_show import ShowTests

if __name__ == "__main__":
    print('=====> Running all test in "sickchill_tests.show" <=====')

    TEST_CLASSES = [
        ComingEpisodesTests,
        HistoryTests,
        ShowTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
