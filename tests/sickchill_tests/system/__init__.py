"""
Tests for SickChill system
"""

import unittest

from .restart_tests import RestartTests
from .shutdown_tests import ShutdownTests

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests.system" <=====')

    TEST_CLASSES = [
        RestartTests,
        ShutdownTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
