"""
Tests for SickChill providers
"""

import unittest

from .test_generic_provider import GenericProviderTests
from .test_nzb_provider import NZBProviderTests
from .test_torrent_provider import TorrentProviderTests

if __name__ == "__main__":
    print('=====> Running all test in "sickchill_tests.providers" <=====')

    TEST_CLASSES = [
        GenericProviderTests,
        NZBProviderTests,
        TorrentProviderTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
