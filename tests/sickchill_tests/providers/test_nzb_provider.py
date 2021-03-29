"""
Test NZBProvider
"""

import os
import unittest

from sickchill import settings
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.nzb.NZBProvider import NZBProvider

from .test_generic_provider import GenericProviderTests


class NZBProviderTests(GenericProviderTests):
    """
    Test NZBProvider
    """

    def test___init__(self):
        """
        Test __init__
        """
        assert NZBProvider("Test Provider").provider_type == GenericProvider.NZB

    def test_is_active(self):
        """
        Test is_active
        """
        test_cases = {
            (False, False): False,
            (False, None): False,
            (False, True): False,
            (None, False): False,
            (None, None): False,
            (None, True): False,
            (True, False): False,
            (True, None): False,
            (True, True): True,
        }

        for ((use_nzb, enabled), result) in test_cases.items():
            settings.USE_NZBS = use_nzb

            provider = NZBProvider("Test Provider")
            provider.enabled = enabled

            assert provider.is_active == result

    def test__get_size(self):
        """
        Test _get_size
        """
        items_list = [
            None,
            {},
            {"links": None},
            {"links": []},
            {"links": [{}]},
            {"links": [{"length": 1}, {"length": None}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": ""}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "0"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "123"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "12.3"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "-123"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "-12.3"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 0}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 123}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 12.3}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": -123}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": -12.3}, {"length": 3}]},
        ]
        results_list = [-1, -1, -1, -1, -1, -1, -1, 0, 123, -1, -123, -1, 0, 123, 12, -123, -12]

        unicode_items_list = [
            {"links": None},
            {"links": []},
            {"links": [{}]},
            {"links": [{"length": 1}, {"length": None}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": ""}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "0"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "123"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "12.3"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "-123"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": "-12.3"}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 0}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 123}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": 12.3}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": -123}, {"length": 3}]},
            {"links": [{"length": 1}, {"length": -12.3}, {"length": 3}]},
        ]
        unicode_results_list = [-1, -1, -1, -1, -1, 0, 123, -1, -123, -1, 0, 123, 12, -123, -12]

        assert len(items_list) == len(results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(items_list), len(results_list))

        assert len(unicode_items_list) == len(unicode_results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(unicode_items_list), len(unicode_results_list))

        for (index, item) in enumerate(items_list):
            assert NZBProvider("Test Provider")._get_size(item) == results_list[index]

        for (index, item) in enumerate(unicode_items_list):
            assert NZBProvider("Test Provider")._get_size(item) == unicode_results_list[index]

    def test__get_storage_dir(self):
        """
        Test _get_storage_dir
        """
        test_cases = [None, 123, 12.3, "", os.path.join("some", "path", "to", "folder")]

        for nzb_dir in test_cases:
            settings.NZB_DIR = nzb_dir

            assert NZBProvider("Test Provider")._get_storage_dir() == nzb_dir


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(NZBProviderTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
