import os
import os.path
import re
import time
from collections import OrderedDict
from operator import attrgetter
from threading import Lock
from typing import TYPE_CHECKING

import dateutil.parser

import sickchill
from sickchill import logger
from sickchill.helper.common import remove_extension
from sickchill.oldbeard import common, db, helpers, scene_exceptions, scene_numbering
from sickchill.oldbeard.name_parser import regexes

if TYPE_CHECKING:
    from typing import List

    from sickchill.tv import TVShow


class NameParser(object):
    ALL_REGEX = 0
    NORMAL_REGEX = 1
    ANIME_REGEX = 2

    def __init__(self, filename: bool = True, showObj=None, tryIndexers: bool = False, naming_pattern: bool = False, parse_method: str = None):

        self.filename: bool = filename
        self.showObj: TVShow = showObj
        self.tryIndexers: bool = tryIndexers
        self.compiled_regexes: List = []

        self.naming_pattern = naming_pattern

        if (self.showObj and not self.showObj.is_anime) or parse_method == "normal":
            self._compile_regexes(self.NORMAL_REGEX)
        elif (self.showObj and self.showObj.is_anime) or parse_method == "anime":
            self._compile_regexes(self.ANIME_REGEX)
        else:
            self._compile_regexes(self.ALL_REGEX)

    @staticmethod
    def clean_series_name(series_name):
        """Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string.
        Stolen from dbr's tvnamer
        """

        series_name = re.sub(r"(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub(r"(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub(r"(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub(r"\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub(r"-$", "", series_name)
        series_name = re.sub(r"^\[.*\]", "", series_name)
        return series_name.strip()

    def _compile_regexes(self, regexMode):
        if regexMode == self.ANIME_REGEX:
            dbg_str = "ANIME"
            uncompiled_regex = [regexes.anime_regexes]
        elif regexMode == self.NORMAL_REGEX:
            dbg_str = "NORMAL"
            uncompiled_regex = [regexes.normal_regexes]
        else:
            dbg_str = "ALL"
            uncompiled_regex = [regexes.normal_regexes, regexes.anime_regexes]

        for regexItem in uncompiled_regex:
            for cur_pattern_num, (cur_pattern_name, cur_pattern) in enumerate(regexItem):
                try:
                    cur_regex = re.compile(cur_pattern, re.VERBOSE | re.I)
                except re.error as errormsg:
                    logger.info(f"WARNING: Invalid episode_pattern using {dbg_str} regexs, {errormsg}. {cur_pattern}")
                else:
                    self.compiled_regexes.append((cur_pattern_num, cur_pattern_name, cur_regex))

    def _parse_string(self, name, skip_scene_detection=False):
        if not name:
            return

        matches = []
        best_result = None

        for (cur_regex_num, cur_regex_name, cur_regex) in self.compiled_regexes:
            match = cur_regex.match(name)

            if not match:
                continue

            result = ParseResult(name)
            result.which_regex = [cur_regex_name]
            result.score = 0 - cur_regex_num

            named_groups = list(match.groupdict())

            if "series_name" in named_groups:
                result.series_name = match.group("series_name")
                if result.series_name:
                    result.series_name = self.clean_series_name(result.series_name)
                    result.score += 1

            if "series_num" in named_groups and match.group("series_num"):
                result.score += 1

            if "season_num" in named_groups:
                tmp_season = int(match.group("season_num"))
                if cur_regex_name == "bare" and tmp_season in (19, 20):
                    continue
                if cur_regex_name == "fov" and tmp_season > 500:
                    continue

                result.season_number = tmp_season
                result.score += 1

            if "ep_num" in named_groups:
                ep_num = self._convert_number(match.group("ep_num"))
                if "extra_ep_num" in named_groups and match.group("extra_ep_num"):
                    tmp_episodes = list(range(ep_num, self._convert_number(match.group("extra_ep_num")) + 1))
                    if len(tmp_episodes) > 4:
                        continue
                else:
                    tmp_episodes = [ep_num]

                result.episode_numbers = tmp_episodes
                result.score += 3

            if "ep_ab_num" in named_groups:
                ep_ab_num = self._convert_number(match.group("ep_ab_num"))
                if "extra_ab_ep_num" in named_groups and match.group("extra_ab_ep_num"):
                    result.ab_episode_numbers = list(range(ep_ab_num, self._convert_number(match.group("extra_ab_ep_num")) + 1))
                    result.score += 1
                else:
                    result.ab_episode_numbers = [ep_ab_num]
                result.score += 1

            if "air_date" in named_groups:
                air_date = match.group("air_date")
                try:
                    # Workaround for shows that get interpreted as 'air_date' incorrectly.
                    # Shows so far are 11.22.63 and 9-1-1
                    excluded_shows = ["112263", "911"]
                    assert re.sub(r"[^\d]*", "", air_date) not in excluded_shows

                    # noinspection PyUnresolvedReferences
                    check = dateutil.parser.parse(air_date, fuzzy_with_tokens=True)[0].date()
                    # Make sure a 20th century date isn't returned as a 21st century date
                    # 1 Year into the future (No releases should be coming out a year ahead of time, that's just insane)
                    if check > check.today() and (check - check.today()).days // 365 > 1:
                        check = check.replace(year=check.year - 100)

                    result.air_date = check
                    result.score += 1
                except Exception as error:
                    logger.debug(error)
                    continue

            if "extra_info" in named_groups:
                tmp_extra_info = match.group("extra_info")

                # Show.S04.Special or Show.S05.Part.2.Extras is almost certainly not every episode in the season
                if tmp_extra_info and cur_regex_name == "season_only" and re.search(r"([. _-]|^)(special|extra)s?\w*([. _-]|$)", tmp_extra_info, re.I):
                    continue
                result.extra_info = tmp_extra_info
                result.score += 1

            if "release_group" in named_groups:
                result.release_group = match.group("release_group")
                result.score += 1

            if "version" in named_groups:
                # assigns version to anime file if detected using anime regex. Non-anime regex receives -1
                version = match.group("version")
                if version:
                    result.version = version
                else:
                    result.version = 1
            else:
                result.version = -1

            matches.append(result)

        # only get matches with series_name
        # TODO: This makes tests fail when checking filenames that do not include the show name (refresh, force update, etc)
        # matches = [x for x in matches if x.series_name]

        if matches:
            # pick best match with highest score based on placement
            best_result = max(sorted(matches, reverse=True, key=attrgetter("which_regex")), key=attrgetter("score"))

            show = None
            if best_result and best_result.series_name and not self.naming_pattern:
                # try and create a show object for this result
                show = helpers.get_show(best_result.series_name, self.tryIndexers)

            # confirm passed in show object indexer id matches result show object indexer id
            if show:
                if self.showObj and show.indexerid != self.showObj.indexerid:
                    show = None
                best_result.show = show
            elif self.showObj and not show:
                best_result.show = self.showObj

            # Only allow anime matches if resolved show or specified show is anime
            best_result = self.check_anime_preferred(best_result, matches)

            # if this is a naming pattern test or result doesn't have a show object then return best result
            if not best_result.show or self.naming_pattern:
                return best_result

            # get quality
            best_result.quality = common.Quality.nameQuality(name, best_result.show.is_anime)

            new_episode_numbers = []
            new_season_numbers = []
            new_absolute_numbers = []

            # if we have an air-by-date show then get the real season/episode numbers
            if best_result.is_air_by_date:
                airdate = best_result.air_date.toordinal()
                main_db_con = db.DBConnection()
                sql_result = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                    [best_result.show.indexerid, best_result.show.indexer, airdate],
                )

                season_number = None
                episode_numbers = []

                if sql_result:
                    season_number = int(sql_result[0][0])
                    episode_numbers = [int(sql_result[0][1])]

                if season_number is None or not episode_numbers:
                    try:
                        epObj = sickchill.indexer.episode(best_result.show, firstAired=best_result.air_date)
                        season_number = epObj["airedSeason"]
                        episode_numbers = [epObj["airedEpisode"]]
                    except Exception:
                        logger.warning(f"Unable to find episode with date {best_result.air_date} for show {best_result.show.name}, skipping")
                        episode_numbers = []

                for epNo in episode_numbers:
                    s = season_number
                    e = epNo

                    if best_result.show.is_scene:
                        (s, e) = scene_numbering.get_indexer_numbering(best_result.show.indexerid, best_result.show.indexer, season_number, epNo)
                    new_episode_numbers.append(e)
                    new_season_numbers.append(s)

            elif best_result.show.is_anime and best_result.ab_episode_numbers:
                best_result.scene_season = scene_exceptions.get_scene_exception_by_name(best_result.series_name)[1]
                for epAbsNo in best_result.ab_episode_numbers:
                    a = epAbsNo

                    if best_result.show.is_scene and not skip_scene_detection:
                        a = scene_numbering.get_indexer_absolute_numbering(
                            best_result.show.indexerid, best_result.show.indexer, epAbsNo, True, best_result.scene_season
                        )

                    (s, e) = helpers.get_all_episodes_from_absolute_number(best_result.show, [a])

                    new_absolute_numbers.append(a)
                    new_episode_numbers.extend(e)
                    new_season_numbers.append(s)

            elif best_result.season_number and best_result.episode_numbers:
                for epNo in best_result.episode_numbers:
                    s = best_result.season_number
                    e = epNo

                    if best_result.show.is_scene and not skip_scene_detection:
                        (s, e) = scene_numbering.get_indexer_numbering(best_result.show.indexerid, best_result.show.indexer, best_result.season_number, epNo)
                    if best_result.show.is_anime:
                        a = helpers.get_absolute_number_from_season_and_episode(best_result.show, s, e)
                        if a:
                            new_absolute_numbers.append(a)

                    new_episode_numbers.append(e)
                    new_season_numbers.append(s)

            # need to do a quick sanity check heregex.  It's possible that we now have episodes
            # from more than one season (by tvdb numbering), and this is just too much
            # for oldbeard, so we'd need to flag it.
            new_season_numbers = list(set(new_season_numbers))  # remove duplicates
            if len(new_season_numbers) > 1:
                raise InvalidNameException(
                    f"Scene numbering results episodes from seasons {new_season_numbers}, (i.e. more than one) and sickchill does not support this. Sorry."
                )

            # I guess it's possible that we'd have duplicate episodes too, so lets
            # eliminate them
            new_episode_numbers = sorted(set(new_episode_numbers))

            # maybe even duplicate absolute numbers so why not do them as well
            new_absolute_numbers = list(set(new_absolute_numbers))
            new_absolute_numbers.sort()

            if new_absolute_numbers:
                best_result.ab_episode_numbers = new_absolute_numbers

            if new_season_numbers and new_episode_numbers:
                best_result.episode_numbers = new_episode_numbers
                best_result.season_number = new_season_numbers[0]

            if best_result.show.is_scene and not skip_scene_detection:
                logger.debug(f"Converted parsed result {best_result.original_name} into {best_result}")

        # CPU sleep
        time.sleep(0.02)

        return best_result

    def check_anime_preferred(self, best_result, matches):
        show = self.showObj or best_result.show
        if (best_result.show and best_result.show.is_anime and not self.showObj) or (self.showObj and self.showObj.is_anime):
            anime_matches = [x for x in matches if "anime" in x.which_regex[0]]
            if anime_matches:
                best_result_anime = max(sorted(anime_matches, reverse=True, key=attrgetter("which_regex")), key=attrgetter("score"))
                if best_result_anime and best_result_anime.series_name:
                    show_anime = helpers.get_show(best_result_anime.series_name)
                    if show_anime and show_anime.indexerid == show.indexerid:
                        best_result_anime.show = show_anime
                        best_result = best_result_anime

        return best_result

    @staticmethod
    def _combine_results(first, second, attr):
        # if the first doesn't exist then return the second or nothing
        if not first:
            if not second:
                return None
            else:
                return getattr(second, attr)

        # if the second doesn't exist then return the first
        if not second:
            return getattr(first, attr)

        a = getattr(first, attr)
        b = getattr(second, attr)

        # if a is good use it
        if a is not None or (isinstance(a, list) and a):
            return a
        # if not use b (if b isn't set it'll just be default)
        else:
            return b

    @staticmethod
    def _unicodify(obj, encoding="utf-8"):
        if isinstance(obj, bytes):
            obj = str(obj, encoding, "replace")
        return obj

    @staticmethod
    def _convert_number(org_number):
        """
        Convert org_number into an integer
        org_number: integer or representation of a number: string or str
        Try force converting to int first, on error try converting from Roman numerals
        returns integer or 0
        """

        try:
            # try forcing to int
            if org_number:
                number = int(org_number)
            else:
                number = 0

        except Exception:
            # on error try converting from Roman numerals
            roman_to_int_map = (
                ("M", 1000),
                ("CM", 900),
                ("D", 500),
                ("CD", 400),
                ("C", 100),
                ("XC", 90),
                ("L", 50),
                ("XL", 40),
                ("X", 10),
                ("IX", 9),
                ("V", 5),
                ("IV", 4),
                ("I", 1),
            )

            roman_numeral = str(org_number).upper()
            number = 0
            index = 0

            for numeral, integer in roman_to_int_map:
                while roman_numeral[index : index + len(numeral)] == numeral:
                    number += integer
                    index += len(numeral)

        return number

    def parse(self, name, cache_result=True, skip_scene_detection=False):
        name = self._unicodify(name)

        if self.naming_pattern:
            cache_result = False

        cached = name_parser_cache[name]
        if cached:
            return cached

        # break it into parts if there are any (dirname, file name, extension)
        dir_name, filename = os.path.split(name)

        if self.filename:
            base_filename = remove_extension(filename)
        else:
            base_filename = filename

        # set up a result to use
        final_result = ParseResult(name)

        # try parsing the file name
        filename_result = self._parse_string(base_filename, skip_scene_detection)

        # use only the direct parent dir
        dir_name = os.path.basename(dir_name)

        # parse the dirname for extra info if needed
        dir_name_result = self._parse_string(dir_name, skip_scene_detection)

        # build the ParseResult object
        final_result.air_date = self._combine_results(filename_result, dir_name_result, "air_date")

        # anime absolute numbers
        final_result.ab_episode_numbers = self._combine_results(filename_result, dir_name_result, "ab_episode_numbers")

        # season and episode numbers
        final_result.season_number = self._combine_results(filename_result, dir_name_result, "season_number")
        final_result.episode_numbers = self._combine_results(filename_result, dir_name_result, "episode_numbers")
        final_result.scene_season = self._combine_results(filename_result, dir_name_result, "scene_season")

        # if the dirname has a release group/show name I believe it over the filename
        final_result.series_name = self._combine_results(dir_name_result, filename_result, "series_name")
        final_result.extra_info = self._combine_results(dir_name_result, filename_result, "extra_info")
        final_result.release_group = self._combine_results(dir_name_result, filename_result, "release_group")
        final_result.version = self._combine_results(dir_name_result, filename_result, "version")

        final_result.which_regex = []
        if final_result == filename_result:
            final_result.which_regex = filename_result.which_regex
            final_result.score = filename_result.score
        elif final_result == dir_name_result:
            final_result.which_regex = dir_name_result.which_regex
            final_result.score = dir_name_result.score
        else:
            final_result.score = 0
            if filename_result:
                final_result.which_regex += filename_result.which_regex
                final_result.score += filename_result.score
            if dir_name_result:
                final_result.which_regex += dir_name_result.which_regex
                final_result.score += dir_name_result.score

        final_result.show = self._combine_results(filename_result, dir_name_result, "show")
        final_result.quality = self._combine_results(filename_result, dir_name_result, "quality")

        if not final_result.show:
            raise InvalidShowException(f"Unable to match {name} to a show in your database. Parser result: {final_result}")

        # if there's no useful info in it then raise an exception
        if (
            final_result.season_number is None
            and not final_result.episode_numbers
            and final_result.air_date is None
            and not final_result.ab_episode_numbers
            and not final_result.series_name
        ):
            raise InvalidNameException(f"Unable to parse {name} to a valid episode of {final_result.show.name}. Parser result: {final_result}")

        if cache_result:
            name_parser_cache[name] = final_result

        logger.debug(f"Parsed {name} into {final_result}")
        return final_result


class ParseResult(object):
    def __init__(
        self,
        original_name,
        series_name=None,
        season_number=None,
        episode_numbers=None,
        extra_info=None,
        release_group=None,
        air_date=None,
        ab_episode_numbers=None,
        show=None,
        score=0,
        quality=None,
        version=None,
    ):

        self.original_name = original_name

        self.series_name = series_name
        self.season_number = season_number
        if not episode_numbers:
            self.episode_numbers = []
        else:
            self.episode_numbers = episode_numbers

        if not ab_episode_numbers:
            self.ab_episode_numbers = []
        else:
            self.ab_episode_numbers = ab_episode_numbers

        if not quality:
            self.quality = common.Quality.UNKNOWN
        else:
            self.quality = quality

        self.extra_info = extra_info
        self.release_group = release_group

        self.air_date = air_date

        self.which_regex = []
        self.show: "TVShow" = show
        self.score = score

        self.version = version

        self.scene_season = None

    def __eq__(self, other):
        return other and all(
            [
                self.series_name == other.series_name,
                self.season_number == other.season_number,
                self.episode_numbers == other.episode_numbers,
                self.extra_info == other.extra_info,
                self.release_group == other.release_group,
                self.air_date == other.air_date,
                self.ab_episode_numbers == other.ab_episode_numbers,
                self.show == other.show,
                self.score == other.score,
                self.quality == other.quality,
                self.version == other.version,
            ]
        )

    def __str__(self):
        if self.series_name is not None:
            to_return = f"{self.series_name} - "
        else:
            to_return = ""
        if self.season_number is not None:
            to_return += f"S{self.season_number:02}"
        if self.episode_numbers:
            for e in self.episode_numbers:
                if e is not None:
                    to_return += f"E{e:02}"

        if self.is_air_by_date:
            to_return += f" {self.air_date}"
        if self.ab_episode_numbers:
            to_return += f" [ABS: {self.ab_episode_numbers}]"
        if self.version and self.is_anime is True:
            to_return += f" [ANIME VER: {self.version}]"

        if self.release_group:
            to_return += f" [GROUP: {self.release_group}]"

        to_return += f" [ABD: {self.is_air_by_date}] [ANIME: {self.is_anime}] [whichReg: {self.which_regex}] Score: {self.score}"

        return re.sub(r"[ ]+", " ", to_return)

    @property
    def is_air_by_date(self):
        return bool(self.air_date)

    @property
    def is_anime(self):
        return bool(self.ab_episode_numbers)


class NameParserCache(object):
    def __init__(self):
        self.lock = Lock()
        self.data = OrderedDict()
        self.max_size = 200

    def __getitem__(self, name):
        with self.lock:
            value = self.data.get(name)
            if value:
                logger.debug(f"Using cached parse result for: {name}")
            return value

    def __setitem__(self, key, value):
        with self.lock:
            self.data.update({key: value})
            while len(self.data) > self.max_size:
                self.data.pop(list(self.data)[0], None)


name_parser_cache = NameParserCache()


class InvalidNameException(Exception):
    """The given release name is not valid"""


class InvalidShowException(Exception):
    """The given show name is not valid"""
