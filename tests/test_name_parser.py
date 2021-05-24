import datetime
import os
import sys
import unittest

from sickchill import tv
from sickchill.oldbeard import common
from sickchill.oldbeard.name_parser import parser
from tests import conftest

DEBUG = os.getenv("DEBUG")
VERBOSE = os.getenv("VERBOSE")

SIMPLE_TEST_CASES = {
    "standard": {
        "Mr.Show.Name.S01E02.Source.Quality.Etc-Group": parser.ParseResult(None, "Mr Show Name", 1, [2], "Source.Quality.Etc", "Group"),
        "Show.Name.S01E02": parser.ParseResult(None, "Show Name", 1, [2]),
        "Show Name - S01E02 - My Ep Name": parser.ParseResult(None, "Show Name", 1, [2], "My Ep Name"),
        "Show.1.0.Name.S01.E03.My.Ep.Name-Group": parser.ParseResult(None, "Show 1.0 Name", 1, [3], "My.Ep.Name", "Group"),
        "Show.Name.S01E02E03.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", 1, [2, 3], "Source.Quality.Etc", "Group"),
        "Mr. Show Name - S01E02-03 - My Ep Name": parser.ParseResult(None, "Mr. Show Name", 1, [2, 3], "My Ep Name"),
        "Show.Name.S01.E02.E03": parser.ParseResult(None, "Show Name", 1, [2, 3]),
        "Show.Name-0.2010.S01E02.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name-0 2010", 1, [2], "Source.Quality.Etc", "Group"),
        "S01E02 Ep Name": parser.ParseResult(None, None, 1, [2], "Ep Name"),
        "Show Name - S06E01 - 2009-12-20 - Ep Name": parser.ParseResult(None, "Show Name", 6, [1], "2009-12-20 - Ep Name"),
        "Show Name - S06E01 - -30-": parser.ParseResult(None, "Show Name", 6, [1], "30-"),
        "Show-Name-S06E01-720p": parser.ParseResult(None, "Show-Name", 6, [1], "720p"),
        "Show-Name-S06E01-1080i": parser.ParseResult(None, "Show-Name", 6, [1], "1080i"),
        "Show.Name.S06E01.Other.WEB-DL": parser.ParseResult(None, "Show Name", 6, [1], "Other.WEB-DL"),
        "Show.Name.S06E01 Some-Stuff Here": parser.ParseResult(None, "Show Name", 6, [1], "Some-Stuff Here"),
        "Show Name - S03E14-36! 24! 36! Hut! (1)": parser.ParseResult(None, "Show Name", 3, [14], "36! 24! 36! Hut! (1)"),
    },
    "fov": {
        "Show_Name.1x02.Source_Quality_Etc-Group": parser.ParseResult(None, "Show Name", 1, [2], "Source_Quality_Etc", "Group"),
        "Show Name 1x02": parser.ParseResult(None, "Show Name", 1, [2]),
        "Show Name 1x02 x264 Test": parser.ParseResult(None, "Show Name", 1, [2], "x264 Test"),
        "Show Name - 1x02 - My Ep Name": parser.ParseResult(None, "Show Name", 1, [2], "My Ep Name"),
        "Show_Name.1x02x03x04.Source_Quality_Etc-Group": parser.ParseResult(None, "Show Name", 1, [2, 3, 4], "Source_Quality_Etc", "Group"),
        "Show Name - 1x02-03-04 - My Ep Name": parser.ParseResult(None, "Show Name", 1, [2, 3, 4], "My Ep Name"),
        "1x02 Ep Name": parser.ParseResult(None, None, 1, [2], "Ep Name"),
        "Show-Name-1x02-720p": parser.ParseResult(None, "Show-Name", 1, [2], "720p"),
        "Show-Name-1x02-1080i": parser.ParseResult(None, "Show-Name", 1, [2], "1080i"),
        "Show Name [05x12] Ep Name": parser.ParseResult(None, "Show Name", 5, [12], "Ep Name"),
        "Show.Name.1x02.WEB-DL": parser.ParseResult(None, "Show Name", 1, [2], "WEB-DL"),
    },
    "standard_repeat": {
        "Show.Name.S01E02.S01E03.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", 1, [2, 3], "Source.Quality.Etc", "Group"),
        "Show.Name.S01E02.S01E03": parser.ParseResult(None, "Show Name", 1, [2, 3]),
        "Show Name - S01E02 - S01E03 - S01E04 - Ep Name": parser.ParseResult(None, "Show Name", 1, [2, 3, 4], "Ep Name"),
        "Show.Name.S01E02.S01E03.WEB-DL": parser.ParseResult(None, "Show Name", 1, [2, 3], "WEB-DL"),
    },
    "fov_repeat": {
        "Show.Name.1x02.1x03.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", 1, [2, 3], "Source.Quality.Etc", "Group"),
        "Show.Name.1x02.1x03": parser.ParseResult(None, "Show Name", 1, [2, 3]),
        "Show Name - 1x02 - 1x03 - 1x04 - Ep Name": parser.ParseResult(None, "Show Name", 1, [2, 3, 4], "Ep Name"),
        "Show.Name.1x02.1x03.WEB-DL": parser.ParseResult(None, "Show Name", 1, [2, 3], "WEB-DL"),
    },
    "bare": {
        "Show.Name.102.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", 1, [2], "Source.Quality.Etc", "Group"),
        "show.name.2010.123.source.quality.etc-group": parser.ParseResult(None, "show name 2010", 1, [23], "source.quality.etc", "group"),
        "show.name.2010.222.123.source.quality.etc-group": parser.ParseResult(None, "show name 2010.222", 1, [23], "source.quality.etc", "group"),
        "Show.Name.102": parser.ParseResult(None, "Show Name", 1, [2]),
        "Show.Name.01e02": parser.ParseResult(None, "Show Name", 1, [2]),
        "the.event.401.hdtv-group": parser.ParseResult(None, "the event", 4, [1], "hdtv", "group"),
        "show.name.2010.special.hdtv-blah": None,
        "show.ex-name.102.hdtv-group": parser.ParseResult(None, "show ex-name", 1, [2], "hdtv", "group"),
    },
    "stupid": {"tpz-abc102": parser.ParseResult(None, "abc", 1, [2], None, "tpz"), "tpz-abc.102": parser.ParseResult(None, "abc", 1, [2], None, "tpz")},
    "no_season": {
        "Show Name - 01 - Ep Name": parser.ParseResult(None, "Show Name", None, [1], "Ep Name"),
        "01 - Ep Name": parser.ParseResult(None, None, None, [1], "Ep Name"),
        "Show Name - 01 - Ep Name - WEB-DL": parser.ParseResult(None, "Show Name", None, [1], "Ep Name - WEB-DL"),
    },
    "no_season_general": {
        "Show.Name.E23.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", None, [23], "Source.Quality.Etc", "Group"),
        "Show Name - Episode 01 - Ep Name": parser.ParseResult(None, "Show Name", None, [1], "Ep Name"),
        "Show.Name.Part.3.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", None, [3], "Source.Quality.Etc", "Group"),
        "Show.Name.Part.1.and.Part.2.Blah-Group": parser.ParseResult(None, "Show Name", None, [1, 2], "Blah", "Group"),
        "Show.Name.Part.IV.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", None, [4], "Source.Quality.Etc", "Group"),
        "Deconstructed.E07.1080i.HDTV.DD5.1.MPEG2-TrollHD": parser.ParseResult(None, "Deconstructed", None, [7], "1080i.HDTV.DD5.1.MPEG2", "TrollHD"),
        "Show.Name.E23.WEB-DL": parser.ParseResult(None, "Show Name", None, [23], "WEB-DL"),
    },
    "no_season_multi_ep": {
        "Show.Name.E23-24.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", None, [23, 24], "Source.Quality.Etc", "Group"),
        "Show Name - Episode 01-02 - Ep Name": parser.ParseResult(None, "Show Name", None, [1, 2], "Ep Name"),
        "Show.Name.E23-24.WEB-DL": parser.ParseResult(None, "Show Name", None, [23, 24], "WEB-DL"),
    },
    "season_only": {
        "Show.Name.S02.Source.Quality.Etc-Group": parser.ParseResult(None, "Show Name", 2, [], "Source.Quality.Etc", "Group"),
        "Show Name Season 2": parser.ParseResult(None, "Show Name", 2),
        "Season 02": parser.ParseResult(None, None, 2),
    },
    "scene_date_format": {
        "Show.Name.2010.11.23.Source.Quality.Etc-Group": parser.ParseResult(
            None, "Show Name", None, [], "Source.Quality.Etc", "Group", datetime.date(2010, 11, 23)
        ),
        "Show Name - 2010.11.23": parser.ParseResult(None, "Show Name", air_date=datetime.date(2010, 11, 23)),
        "Show.Name.2010.23.11.Source.Quality.Etc-Group": parser.ParseResult(
            None, "Show Name", None, [], "Source.Quality.Etc", "Group", datetime.date(2010, 11, 23)
        ),
        "Show Name - 2010-11-23 - Ep Name": parser.ParseResult(None, "Show Name", extra_info="Ep Name", air_date=datetime.date(2010, 11, 23)),
        "2010-11-23 - Ep Name": parser.ParseResult(None, extra_info="Ep Name", air_date=datetime.date(2010, 11, 23)),
        "Show.Name.2010.11.23.WEB-DL": parser.ParseResult(None, "Show Name", None, [], "WEB-DL", None, datetime.date(2010, 11, 23)),
    },
}

ANIME_TEST_CASES = {
    "anime_SxxExx": {
        "Show Name - S01E02 - Ep Name": parser.ParseResult(None, "Show Name", 1, [2], "Ep Name"),
        "Show Name - S01E02-03 - My Ep Name": parser.ParseResult(None, "Show Name", 1, [2, 3]),
        "Show Name - S01E02": parser.ParseResult(None, "Show Name", 1, [2]),
        "Show Name - S01E02-03": parser.ParseResult(None, "Show Name", 1, [2, 3]),
    },
    "anime_bare": {
        "Show Name - 102": parser.ParseResult(None, "Show Name", ab_episode_numbers=[102], version=1),
        "[SC]_Show_Name_123": parser.ParseResult(None, "Show Name", release_group="SC", ab_episode_numbers=[123], version=1),
        "Show.Name.-.134.-.1080p.BluRay.x264.DHD": parser.ParseResult(
            None, "Show Name", ab_episode_numbers=[134], quality=common.Quality.FULLHDBLURAY, version=1
        ),
    },
}

COMBINATION_TEST_CASES = [
    ("/test/path/to/Season 02/03 - Ep Name.avi", parser.ParseResult(None, None, 2, [3], "Ep Name"), ["no_season", "season_only"]),
    (
        "Show.Name.S02.Source.Quality.Etc-Group/tpz-sn203.avi",
        parser.ParseResult(None, "Show Name", 2, [3], "Source.Quality.Etc", "Group"),
        ["stupid", "season_only"],
    ),
    ("MythBusters.S08E16.720p.HDTV.x264-aAF/aaf-mb.s08e16.720p.mkv", parser.ParseResult(None, "MythBusters", 8, [16], "720p.HDTV.x264", "aAF"), ["standard"]),
    (
        "/home/drop/storage/TV/Terminator The Sarah Connor Chronicles/Season 2/S02E06 The Tower is Tall, But the Fall is Short.mkv",
        parser.ParseResult(None, None, 2, [6], "The Tower is Tall, But the Fall is Short"),
        ["standard"],
    ),
    (
        r"/Test/TV/Jimmy Fallon/Season 2/Jimmy Fallon - 2010-12-15 - blah.avi",
        parser.ParseResult(None, "Jimmy Fallon", extra_info="blah", air_date=datetime.date(2010, 12, 15)),
        ["scene_date_format"],
    ),
    (r"/X/30 Rock/Season 4/30 Rock - 4x22 -.avi", parser.ParseResult(None, "30 Rock", 4, [22]), ["fov"]),
    ("Season 2\\Show Name - 03-04 - Ep Name.ext", parser.ParseResult(None, "Show Name", 2, [3, 4], extra_info="Ep Name"), ["no_season", "season_only"]),
    ("Season 02\\03-04-05 - Ep Name.ext", parser.ParseResult(None, None, 2, [3, 4, 5], extra_info="Ep Name"), ["no_season", "season_only"]),
]

UNICODE_TEST_CASES = [
    (
        "The.Big.Bang.Theory.2x07.The.Panty.Piñata.Polarization.720p.HDTV.x264.AC3-SHELDON.mkv",
        parser.ParseResult(None, "The.Big.Bang.Theory", 2, [7], "The.Panty.Piñata.Polarization.720p.HDTV.x264.AC3", "SHELDON"),
    ),
    (
        "The.Big.Bang.Theory.2x07.The.Panty.Piñata.Polarization.720p.HDTV.x264.AC3-SHELDON.mkv",
        parser.ParseResult(None, "The.Big.Bang.Theory", 2, [7], "The.Panty.Piñata.Polarization.720p.HDTV.x264.AC3", "SHELDON"),
    ),
]

FAILURE_CASES = ["7sins-jfcs01e09-720p-bluray-x264"]


class UnicodeTests(conftest.SickChillTestDBCase):
    """
    Test str
    """

    def __init__(self, something):
        super().__init__(something)
        super().setUp()
        self.show = tv.TVShow(1, 1, "en")
        self.show.name = "The Big Bang Theory"

    def _test_unicode(self, name, result):
        """
        Test str

        :param name:
        :param result:
        :return:
        """
        name_parser = parser.NameParser(True, showObj=self.show)
        parse_result = name_parser.parse(name)

        # this shouldn't raise an exception
        repr(str(parse_result))
        assert parse_result.extra_info == result.extra_info

    def test_unicode(self):
        """
        Test str
        """
        for (name, result) in UNICODE_TEST_CASES:
            self._test_unicode(name, result)


class FailureCaseTests(conftest.SickChillTestDBCase):
    """
    Test cases that should fail
    """

    @staticmethod
    def _test_name(name):
        """
        Test name

        :param name:
        :return:
        """
        name_parser = parser.NameParser(True)
        try:
            parse_result = name_parser.parse(name)
        except (parser.InvalidNameException, parser.InvalidShowException):
            return True

        if VERBOSE:
            print("Actual: ", parse_result.which_regex, parse_result)
        return False

    def test_failures(self):
        """
        Test failures
        """
        for name in FAILURE_CASES:
            assert self._test_name(name)


class ComboTests(conftest.SickChillTestDBCase):
    """
    Perform combination tests
    """

    def _test_combo(self, name, result, which_regexes):
        """
        Perform combination test

        :param name:
        :param result:
        :param which_regexes:
        :return:
        """

        if VERBOSE:
            print()
            print("Testing", name)

        name_parser = parser.NameParser(True)

        try:
            test_result = name_parser.parse(name)
        except parser.InvalidShowException:
            return False

        if DEBUG:
            print(test_result, test_result.which_regex)
            print(result, which_regexes)

        assert str(test_result) == str(result)
        for cur_regex in which_regexes:
            assert cur_regex in test_result.which_regex
        assert len(which_regexes) == len(test_result.which_regex)

    def test_combos(self):
        """
        Perform combination tests
        """
        for (name, result, which_regexes) in COMBINATION_TEST_CASES:
            # Normalise the paths. Converts UNIX-style paths into Windows-style
            # paths when test is run on Windows.
            self._test_combo(os.path.normpath(name), result, which_regexes)


class BasicTests(conftest.SickChillTestDBCase):
    """
    Basic name parsing tests
    """

    def __init__(self, something):
        super().__init__(something)
        super().setUp()
        self.show = tv.TVShow(1, 1, "en")

    def _test_names(self, name_parser, section, transform=None, verbose=False):
        """
        Performs a test

        :param name_parser: to use for test
        :param section:
        :param transform:
        :param verbose:
        :return:
        """

        if VERBOSE or verbose:
            print()
            print("Running", section, "tests")
        for cur_test_base in SIMPLE_TEST_CASES[section]:
            if transform:
                cur_test = transform(cur_test_base)
                name_parser.filename = cur_test
            else:
                cur_test = cur_test_base
            if VERBOSE or verbose:
                print("Testing", cur_test)

            result = SIMPLE_TEST_CASES[section][cur_test_base]

            self.show.name = result.series_name if result else None
            name_parser.showObj = self.show
            if not result:
                self.assertRaises(parser.InvalidNameException, name_parser.parse, cur_test)
                return
            else:
                result.which_regex = [section]
                test_result = name_parser.parse(cur_test)

            def print_debug():
                print(f"{cur_test}:")
                print(f"Test Result: {test_result}")
                print(f"Expected Result: {result}")

            if DEBUG or verbose:
                print_debug()

            result.score = test_result.score  # Needed so we don't have to specify expected regex score in each test case.
            assert test_result.which_regex == [section], print_debug()
            assert str(test_result) == str(result), print_debug()

    def test_standard_names(self):
        """
        Test standard names
        """
        name_parser = parser.NameParser(True)
        self._test_names(name_parser, "standard")

    def test_standard_filenames(self):
        """
        Test standard file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "standard", lambda x: x + ".avi")

    def test_standard_repeat_names(self):
        """
        Test standard repeat names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "standard_repeat")

    def test_standard_repeat_filenames(self):
        """
        Test standard repeat file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "standard_repeat", lambda x: x + ".avi")

    def test_fov_names(self):
        """
        Test fov names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "fov")

    def test_fov_filenames(self):
        """
        Test fov file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "fov", lambda x: x + ".avi")

    def test_fov_repeat_names(self):
        """
        Test fov repeat names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "fov_repeat")

    def test_fov_repeat_filenames(self):
        """
        Test fov repeat file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "fov_repeat", lambda x: x + ".avi")

    def test_stupid_names(self):
        """
        Test stupid names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "stupid")

    def test_stupid_filenames(self):
        """
        Test stupid file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "stupid", lambda x: x + ".avi")

    def test_no_s_general_names(self):
        """
        Test no season general names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "no_season_general")

    def test_no_s_general_filenames(self):
        """
        Test no season general file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "no_season_general", lambda x: x + ".avi")

    def test_no_s_multi_ep_names(self):
        """
        Test no season multi episode names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "no_season_multi_ep")

    def test_no_s_multi_ep_filenames(self):
        """
        Test no season multi episode file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "no_season_multi_ep", lambda x: x + ".avi")

    def test_s_only_names(self):
        """
        Test season only names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "season_only")

    def test_s_only_filenames(self):
        """
        Test season only file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "season_only", lambda x: x + ".avi")


class AnimeTests(conftest.SickChillTestDBCase):
    """
    Basic tests for anime
    """

    def __init__(self, something):
        super().__init__(something)
        super().setUp()
        self.show = tv.TVShow(1, 1, "en")
        self.show.anime = True

    def tearDown(self):
        parser.name_parser_cache.data.clear()

    def _test_names(self, name_parser, section, transform=None, verbose=False):
        """
        Performs a test

        :param name_parser: to use for test
        :param section:
        :param transform:
        :param verbose:
        :return:
        """
        if VERBOSE or verbose:
            print()
            print("Running", section, "tests")
        for cur_test_base in ANIME_TEST_CASES[section]:
            if transform:
                cur_test = transform(cur_test_base)
                name_parser.filename = cur_test
            else:
                cur_test = cur_test_base
            if VERBOSE or verbose:
                print("Testing", cur_test)

            result = ANIME_TEST_CASES[section][cur_test_base]

            self.show.name = result.series_name if result else None
            name_parser.showObj = self.show
            if not result:
                self.assertRaises(parser.InvalidNameException, name_parser.parse, cur_test)
                return
            else:
                result.which_regex = [section]
                test_result = name_parser.parse(cur_test)

            def print_debug():
                print(f"{cur_test}:")
                print(f"Test Result: {test_result}")
                print(f"Expected Result: {result}")

            if DEBUG or verbose:
                print_debug()

            result.score = test_result.score  # Needed so we don't have to specify expected regex score in each test case.
            assert test_result.which_regex == [section], print_debug()
            assert str(test_result) == str(result), print_debug()

    def test_anime_sxxexx_filenames(self):
        """
        Test anime SxxExx file names
        """
        name_parser = parser.NameParser(parse_method="anime")
        self._test_names(name_parser, "anime_SxxExx", lambda x: x + ".avi")

    def test_anime_bare_filenames(self):
        """
        Test anime bare file names
        """
        name_parser = parser.NameParser(parse_method="anime")
        self._test_names(name_parser, "anime_bare", lambda x: x + ".avi")

    @unittest.expectedFailure
    def test_anime_bare_filenames_indirect(self):
        """
        Test anime bare file names without defining parse method
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "anime_bare", lambda x: x + ".avi")


# TODO: Make these work or document why they shouldn't
class BasicFailedTests(conftest.SickChillTestDBCase):
    """
    Basic tests that currently fail
    """

    def __init__(self, something):
        super().__init__(something)
        super().setUp()
        self.show = tv.TVShow(1, 1, "en")

    def _test_names(self, name_parser, section, transform=None, verbose=False):
        """
        Performs a test

        :param name_parser: to use for test
        :param section:
        :param transform:
        :param verbose:
        :return:
        """
        if VERBOSE or verbose:
            print()
            print("Running", section, "tests")
        for cur_test_base in SIMPLE_TEST_CASES[section]:
            if transform:
                cur_test = transform(cur_test_base)
                name_parser.filename = cur_test
            else:
                cur_test = cur_test_base
            if VERBOSE or verbose:
                print("Testing", cur_test)

            result = SIMPLE_TEST_CASES[section][cur_test_base]

            self.show.name = result.series_name if result else None
            name_parser.showObj = self.show
            if not result:
                self.assertRaises(parser.InvalidNameException, name_parser.parse, cur_test)
                return
            else:
                result.which_regex = [section]
                test_result = name_parser.parse(cur_test)

            def print_debug():
                print(f"{cur_test}:")
                print(f"Test Result: {test_result}")
                print(f"Expected Result: {result}")

            if DEBUG or verbose:
                print_debug()

            result.score = test_result.score  # Needed so we don't have to specify expected regex score in each test case.
            assert test_result.which_regex == [section], print_debug()
            assert str(test_result) == str(result), print_debug()

    def test_no_s_names(self):
        """
        Test no season names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "no_season")

    def test_no_s_filenames(self):
        """
        Test no season file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "no_season", lambda x: x + ".avi")

    @unittest.expectedFailure
    def test_bare_names(self):
        """
        Test bare names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "bare")

    @unittest.expectedFailure
    def test_bare_filenames(self):
        """
        Test bare file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "bare", lambda x: x + ".avi")

    @unittest.skip("Not yet implemented")
    def test_combination_names(self):
        """
        Test combination names
        """
        pass

    @unittest.skip("Not trying indexer")
    def test_scene_date_fmt_names(self):
        """
        Test scene date format names
        """
        name_parser = parser.NameParser(False)
        self._test_names(name_parser, "scene_date_format")

    @unittest.skip("Not trying indexer")
    def test_scene_date_fmt_filenames(self):
        """
        Test scene date format file names
        """
        name_parser = parser.NameParser()
        self._test_names(name_parser, "scene_date_format", lambda x: x + ".avi")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        SUITE = unittest.TestLoader().loadTestsFromName("name_parser_tests.BasicTests.test_" + sys.argv[1])
        unittest.TextTestRunner(verbosity=2).run(SUITE)
    else:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(BasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ComboTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(UnicodeTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(FailureCaseTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(AnimeTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
