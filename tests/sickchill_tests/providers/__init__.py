"""
Tests for SickChill providers
"""

import unittest

from .generic_provider_tests import GenericProviderTests
from .nzb_provider_tests import NZBProviderTests
from .torrent_provider_tests import TorrentProviderTests

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests.providers" <=====')

    TEST_CLASSES = [
        GenericProviderTests,
        NZBProviderTests,
        TorrentProviderTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
