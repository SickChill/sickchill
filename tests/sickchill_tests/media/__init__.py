# coding=utf-8
"""
Tests for SickChill media
"""

import unittest

from generic_media_tests import GenericMediaTests
from show_banner_tests import ShowBannerTests
from show_fan_art_tests import ShowFanArtTests
from show_network_logo_tests import ShowNetworkLogoTests
from show_poster_tests import ShowPosterTests

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests.media" <=====')

    TEST_CLASSES = [
        GenericMediaTests,
        ShowBannerTests,
        ShowFanArtTests,
        ShowNetworkLogoTests,
        ShowPosterTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
