"""
Test sickchill.common
"""

import glob
import unittest

from sickchill import settings
from sickchill.helper.common import (
    convert_size,
    episode_num,
    http_code_description,
    is_sync_file,
    is_torrent_or_nzb_file,
    pretty_file_size,
    remove_extension,
    replace_extension,
    sanitize_filename,
    try_int,
)


class CommonTests(unittest.TestCase):
    """
    Test common
    """

    def test_http_code_description(self):
        test_cases = {
            None: None,
            "": None,
            "123": None,
            "12.3": None,
            "-123": None,
            "-12.3": None,
            "300": "Multiple Choices",
            0: None,
            123: None,
            12.3: None,
            -123: None,
            -12.3: None,
            300: "Multiple Choices",
            451: "(Redirect, Unavailable For Legal Reasons)",
            497: "HTTP to HTTPS",
            499: "(Client Closed Request, Token required)",
            600: None,
        }

        unicode_test_cases = {
            "": None,
            "123": None,
            "12.3": None,
            "-123": None,
            "-12.3": None,
            "300": "Multiple Choices",
        }

        for test in test_cases, unicode_test_cases:
            for (http_code, result) in test.items():
                assert http_code_description(http_code) == result

    def test_is_sync_file(self):
        """
        Test is sync file
        """
        settings.SYNC_FILES = "!sync,lftp-pget-status"

        test_cases = {
            None: False,
            42: False,
            "": False,
            "filename": False,
            ".syncthingfilename": True,
            ".syncthing.filename": True,
            ".syncthing-filename": True,
            ".!sync": True,
            "file.!sync": True,
            "file.!sync.ext": False,
            ".lftp-pget-status": True,
            "file.lftp-pget-status": True,
            "file.lftp-pget-status.ext": False,
            ".part": False,
            "file.part": False,
            "file.part.ext": False,
        }

        unicode_test_cases = {
            "": False,
            "filename": False,
            ".syncthingfilename": True,
            ".syncthing.filename": True,
            ".syncthing-filename": True,
            ".!sync": True,
            "file.!sync": True,
            "file.!sync.ext": False,
            ".lftp-pget-status": True,
            "file.lftp-pget-status": True,
            "file.lftp-pget-status.ext": False,
            ".part": False,
            "file.part": False,
            "file.part.ext": False,
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.items():
                assert is_sync_file(filename) == result

    def test_is_torrent_or_nzb_file(self):
        """
        Test is torrent or nzb file
        """
        test_cases = {
            None: False,
            42: False,
            "": False,
            "filename": False,
            ".nzb": True,
            "file.nzb": True,
            "file.nzb.part": False,
            ".torrent": True,
            "file.torrent": True,
            "file.torrent.part": False,
        }

        unicode_test_cases = {
            "": False,
            "filename": False,
            ".nzb": True,
            "file.nzb": True,
            "file.nzb.part": False,
            ".torrent": True,
            "file.torrent": True,
            "file.torrent.part": False,
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.items():
                assert is_torrent_or_nzb_file(filename) == result

    def test_pretty_file_size(self):
        """
        Test pretty file size
        """
        test_cases = {
            None: "0.00 B",
            "": "0.00 B",
            "1024": "1.00 KB",
            "1024.5": "1.00 KB",
            -42.5: "0.00 B",
            -42: "0.00 B",
            0: "0.00 B",
            25: "25.00 B",
            25.5: "25.50 B",
            2 ** 10: "1.00 KB",
            50 * 2 ** 10 + 25: "50.02 KB",
            2 ** 20: "1.00 MB",
            100 * 2 ** 20 + 50 * 2 ** 10 + 25: "100.05 MB",
            2 ** 30: "1.00 GB",
            200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: "200.10 GB",
            2 ** 40: "1.00 TB",
            400 * 2 ** 40 + 200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: "400.20 TB",
            2 ** 50: "1.00 PB",
            800 * 2 ** 50 + 400 * 2 ** 40 + 200 * 2 ** 30 + 100 * 2 ** 20 + 50 * 2 ** 10 + 25: "800.39 PB",
            2 ** 60: 2 ** 60,
        }

        unicode_test_cases = {
            "": "0.00 B",
            "1024": "1.00 KB",
            "1024.5": "1.00 KB",
        }

        for tests in test_cases, unicode_test_cases:
            for (size, result) in tests.items():
                assert pretty_file_size(size) == result

    def test_remove_extension(self):
        """
        Test remove extension
        """
        test_cases = {
            None: None,
            42: 42,
            "": "",
            ".": ".",
            "filename": "filename",
            ".bashrc": ".bashrc",
            ".nzb": ".nzb",
            "file.nzb": "file",
            "file.name.nzb": "file.name",
            ".torrent": ".torrent",
            "file.torrent": "file",
            "file.name.torrent": "file.name",
            ".avi": ".avi",
            "file.avi": "file",
            "file.name.avi": "file.name",
        }

        unicode_test_cases = {
            "": "",
            ".": ".",
            "filename": "filename",
            ".bashrc": ".bashrc",
            ".nzb": ".nzb",
            "file.nzb": "file",
            "file.name.nzb": "file.name",
            ".torrent": ".torrent",
            "file.torrent": "file",
            "file.name.torrent": "file.name",
            ".avi": ".avi",
            "file.avi": "file",
            "file.name.avi": "file.name",
        }
        for tests in test_cases, unicode_test_cases:
            for (extension, result) in tests.items():
                assert remove_extension(extension) == result

    def test_replace_extension(self):
        """
        Test replace extension
        """
        test_cases = {
            (None, None): None,
            (None, ""): None,
            (42, None): 42,
            (42, ""): 42,
            ("", None): "",
            ("", ""): "",
            (".", None): ".",
            (".", ""): ".",
            (".", "avi"): ".",
            ("filename", None): "filename",
            ("filename", ""): "filename",
            ("filename", "avi"): "filename",
            (".bashrc", None): ".bashrc",
            (".bashrc", ""): ".bashrc",
            (".bashrc", "avi"): ".bashrc",
            ("file.mkv", None): "file.None",
            ("file.mkv", ""): "file.",
            ("file.mkv", "avi"): "file.avi",
            ("file.name.mkv", None): "file.name.None",
            ("file.name.mkv", ""): "file.name.",
            ("file.name.mkv", "avi"): "file.name.avi",
        }

        unicode_test_cases = {
            (None, ""): None,
            (42, ""): 42,
            ("", ""): "",
            ("", None): "",
            ("", ""): "",
            ("", ""): "",
            (".", ""): ".",
            (".", "avi"): ".",
            (".", None): ".",
            (".", ""): ".",
            (".", ""): ".",
            (".", "avi"): ".",
            (".", "avi"): ".",
            ("filename", ""): "filename",
            ("filename", "avi"): "filename",
            ("filename", None): "filename",
            ("filename", ""): "filename",
            ("filename", ""): "filename",
            ("filename", "avi"): "filename",
            ("filename", "avi"): "filename",
            (".bashrc", ""): ".bashrc",
            (".bashrc", "avi"): ".bashrc",
            (".bashrc", None): ".bashrc",
            (".bashrc", ""): ".bashrc",
            (".bashrc", ""): ".bashrc",
            (".bashrc", "avi"): ".bashrc",
            (".bashrc", "avi"): ".bashrc",
            ("file.mkv", ""): "file.",
            ("file.mkv", "avi"): "file.avi",
            ("file.mkv", None): "file.None",
            ("file.mkv", ""): "file.",
            ("file.mkv", ""): "file.",
            ("file.mkv", "avi"): "file.avi",
            ("file.mkv", "avi"): "file.avi",
            ("file.name.mkv", ""): "file.name.",
            ("file.name.mkv", "avi"): "file.name.avi",
            ("file.name.mkv", None): "file.name.None",
            ("file.name.mkv", ""): "file.name.",
            ("file.name.mkv", ""): "file.name.",
            ("file.name.mkv", "avi"): "file.name.avi",
            ("file.name.mkv", "avi"): "file.name.avi",
        }

        for tests in test_cases, unicode_test_cases:
            for ((filename, extension), result) in tests.items():
                assert replace_extension(filename, extension) == result

    def test_sanitize_filename(self):
        """
        Test sanitize filename
        """
        # noinspection PyByteLiteral
        # pylint: noqa
        test_cases = {
            None: "",
            42: "",
            b"": "",
            b"filename": "filename",
            b"fi\\le/na*me": "fi-le-na-me",
            b'fi:le"na<me': "filename",
            b"fi>le|na?me": "filename",
            b" . file\u2122name. .": "filename",
        }

        unicode_test_cases = {
            "": "",
            "filename": "filename",
            "fi\\le/na*me": "fi-le-na-me",
            'fi:le"na<me': "filename",
            "fi>le|na?me": "filename",
            " . file™name. .": "filename",
        }

        for tests in test_cases, unicode_test_cases:
            for (filename, result) in tests.items():
                assert sanitize_filename(filename) == result

    def test_try_int(self):
        """
        Test try int
        """
        test_cases = {
            None: 0,
            "": 0,
            "123": 123,
            "-123": -123,
            "12.3": 0,
            "-12.3": 0,
            0: 0,
            123: 123,
            -123: -123,
            12.3: 12,
            -12.3: -12,
        }

        unicode_test_cases = {
            "": 0,
            "123": 123,
            "-123": -123,
            "12.3": 0,
            "-12.3": 0,
        }

        for test in test_cases, unicode_test_cases:
            for (candidate, result) in test.items():
                assert try_int(candidate) == result

    def test_try_int_with_default(self):
        """
        Test try int
        """
        default_value = 42
        test_cases = {
            None: default_value,
            "": default_value,
            "123": 123,
            "-123": -123,
            "12.3": default_value,
            "-12.3": default_value,
            0: 0,
            123: 123,
            -123: -123,
            12.3: 12,
            -12.3: -12,
        }

        unicode_test_cases = {
            "": default_value,
            "123": 123,
            "-123": -123,
            "12.3": default_value,
            "-12.3": default_value,
        }

        for test in test_cases, unicode_test_cases:
            for (candidate, result) in test.items():
                assert try_int(candidate, default_value) == result

    def test_convert_size(self):
        """
        Test convert_size
        """
        # converts pretty file sizes to integers
        assert convert_size("1 B") == 1
        assert convert_size("1 KB") == 1024
        assert convert_size("1 kb", use_decimal=True) == 1000  # can use decimal units (e.g. KB = 1000 bytes instead of 1024)

        # returns integer sizes for integers
        assert convert_size(0, -1) == 0
        assert convert_size(100, -1) == 100
        assert convert_size(1.312, -1) == 1  # returns integer sizes for floats too

        # without a default value, failures return None
        assert convert_size("pancakes") is None

        # default value can be anything
        assert convert_size(None, -1) == -1
        assert convert_size("", 3.14) == 3.14
        assert convert_size("elephant", "frog") == "frog"

        # negative sizes return 0
        assert convert_size(-1024, -1) == 0
        assert convert_size("-1 GB", -1) == 0

        # can also use `or` for a default value
        assert convert_size(None) or 100 == 100
        assert convert_size(None) or 1.61803 == 1.61803  # default doesn't have to be integer
        assert convert_size(None) or "100" == "100"  # default doesn't have to be numeric either
        assert convert_size("-1 GB") or -1 == -1  # can use `or` to provide a default when size evaluates to 0

        # default units can be kwarg'd
        assert convert_size("1", default_units="GB") == convert_size("1 GB")

        # separator can be kwarg'd
        assert convert_size("1?GB", sep="?") == convert_size("1 GB")

        # can use custom dictionary to support internationalization
        french = ["O", "KO", "MO", "GO", "TO", "PO"]
        assert convert_size("1 o", units=french) == 1
        assert convert_size("1 go", use_decimal=True, units=french) == 1000000000
        assert convert_size("1 o") is None  # Wrong units so result is None

        # custom units need to be uppercase or they won't match
        oops = ["b", "kb", "Mb", "Gb", "tB", "Pb"]
        assert convert_size("1 b", units=oops) is None
        assert convert_size("1 B", units=oops) is None
        assert convert_size("1 Mb", units=oops) is None
        assert convert_size("1 MB", units=oops) is None

    def test_episode_num(self):
        # Standard numbering
        assert episode_num(0, 1) == "S00E01"  # Seasons start at 0 for specials
        assert episode_num(1, 1) == "S01E01"

        # Absolute numbering
        assert episode_num(1, numbering="absolute") == "001"
        assert episode_num(0, 1, numbering="absolute") == "001"
        assert episode_num(1, 0, numbering="absolute") == "001"

        # Must have both season and episode for standard numbering
        assert episode_num(0) is None
        assert episode_num(1) is None

        # Episode numbering starts at 1
        assert episode_num(0, 0) is None
        assert episode_num(1, 0) is None

        # Absolute numbering starts at 1
        assert episode_num(0, 0, numbering="absolute") is None

        # Absolute numbering can't have both season and episode
        assert episode_num(1, 1, numbering="absolute") is None

    def test_glob_escape(self):
        assert glob.escape("S01E01 - Show Name [SickChill].avi") == "S01E01 - Show Name [[]SickChill].avi"
        assert glob.escape("S01E01 - Show Name [SickChill].avi") == "S01E01 - Show Name [[]SickChill].avi"
        assert glob.escape("S01E01 - Show Name [SickChill].avi") == "S01E01 - Show Name [[]SickChill].avi"
        assert glob.escape("S01E01 - Show Name [SickChill].avi") == "S01E01 - Show Name [[]SickChill].avi"


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(CommonTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
