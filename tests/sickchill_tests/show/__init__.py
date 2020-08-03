"""
Tests for SickChill show
"""

# Stdlib Imports
import unittest

# Local Folder Imports
from .coming_episodes_tests import ComingEpisodesTests
from .history_tests import HistoryTests
from .show_tests import ShowTests

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests.show" <=====')

    TEST_CLASSES = [
        ComingEpisodesTests,
        HistoryTests,
        ShowTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
