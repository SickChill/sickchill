"""
Test TorrentProvider
"""

import os
import unittest

from sickchill import settings
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.torrent.TorrentProvider import TorrentProvider

from .test_generic_provider import GenericProviderTests


class TorrentProviderTests(GenericProviderTests):
    """
    Test TorrentProvider
    """

    def test___init__(self):
        """
        Test __init__
        """
        assert TorrentProvider("Test Provider").provider_type == GenericProvider.TORRENT

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

        for ((use_torrents, enabled), result) in test_cases.items():
            settings.USE_TORRENTS = use_torrents

            provider = TorrentProvider("Test Provider")
            provider.enabled = enabled

            assert provider.is_active == result

    def test__get_size(self):
        """
        Test _get_size
        """
        items_list = [
            None,
            {},
            {"size": None},
            {"size": ""},
            {"size": "0"},
            {"size": "123"},
            {"size": "12.3"},
            {"size": "-123"},
            {"size": "-12.3"},
            {"size": "1100000"},
            {"size": 0},
            {"size": 123},
            {"size": 12.3},
            {"size": -123},
            {"size": -12.3},
            {"size": 1100000},
            [],
            [None],
            [1100000],
            [None, None, None],
            [None, None, ""],
            [None, None, "0"],
            [None, None, "123"],
            [None, None, "12.3"],
            [None, None, "-123"],
            [None, None, "-12.3"],
            [None, None, "1100000"],
            [None, None, 0],
            [None, None, 123],
            [None, None, 12.3],
            [None, None, -123],
            [None, None, -12.3],
            [None, None, 1100000],
            (),
            (None, None, None),
            (None, None, ""),
            (None, None, "0"),
            (None, None, "123"),
            (None, None, "12.3"),
            (None, None, "-123"),
            (None, None, "-12.3"),
            (None, None, "1100000"),
            "",
            "0",
            "123",
            "12.3",
            "-123",
            "-12.3",
            "1100000",
            0,
            123,
            12.3,
            -123,
            -12.3,
            1100000,
        ]
        results_list = [
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            1100000,
            -1,
            -1,
            -1,
            -1,
            -1,
            1100000,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            1100000,
            -1,
            -1,
            -1,
            -1,
            -1,
            1100000,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            1100000,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
        ]

        assert len(items_list) == len(results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(items_list), len(results_list))

        for (index, item) in enumerate(items_list):
            assert TorrentProvider("Test Provider")._get_size(item) == results_list[index]

    def test__get_storage_dir(self):
        """
        Test _get_storage_dir
        """
        test_cases = [None, 123, 12.3, "", os.path.join("some", "path", "to", "folder")]

        for torrent_dir in test_cases:
            settings.TORRENT_DIR = torrent_dir

            assert TorrentProvider("Test Provider")._get_storage_dir() == torrent_dir


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(TorrentProviderTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
