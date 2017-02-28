# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import os
import os.path
import re
import time
from collections import OrderedDict
from threading import Lock

import dateutil
import six

import sickbeard
from sickbeard import common, db, helpers, logger, scene_exceptions, scene_numbering
from sickbeard.name_parser import regexes
from sickrage.helper.common import remove_extension
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex


class NameParser(object):
    ALL_REGEX = 0
    NORMAL_REGEX = 1
    ANIME_REGEX = 2

    def __init__(self, file_name=True, showObj=None, tryIndexers=False,  # pylint: disable=too-many-arguments
                 naming_pattern=False, parse_method=None):

        self.file_name = file_name
        self.showObj = showObj
        self.tryIndexers = tryIndexers

        self.naming_pattern = naming_pattern

        if (self.showObj and not self.showObj.is_anime) or parse_method == 'normal':
            self._compile_regexes(self.NORMAL_REGEX)
        elif (self.showObj and self.showObj.is_anime) or parse_method == 'anime':
            self._compile_regexes(self.ANIME_REGEX)
        else:
            self._compile_regexes(self.ALL_REGEX)

    @staticmethod
    def clean_series_name(series_name):
        """Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string, for example:

        >>> cleanRegexedSeriesName("an.example.1.0.test")
        'an example 1.0 test'
        >>> cleanRegexedSeriesName("an_example_1.0_test")
        'an example 1.0 test'

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

        self.compiled_regexes = []
        for regexItem in uncompiled_regex:
            for cur_pattern_num, (cur_pattern_name, cur_pattern) in enumerate(regexItem):
                try:
                    cur_regex = re.compile(cur_pattern, re.VERBOSE | re.I)
                except re.error as errormsg:
                    logger.log("WARNING: Invalid episode_pattern using {0} regexs, {1}. {2}".format(dbg_str, errormsg, cur_pattern))
                else:
                    self.compiled_regexes.append((cur_pattern_num, cur_pattern_name, cur_regex))

    def _parse_string(self, name, skip_scene_detection=False):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        if not name:
            return

        matches = []
        bestResult = None

        for (cur_regex_num, cur_regex_name, cur_regex) in self.compiled_regexes:
            match = cur_regex.match(name)

            if not match:
                continue

            result = ParseResult(name)
            result.which_regex = [cur_regex_name]
            result.score = 0 - cur_regex_num

            named_groups = match.groupdict().keys()

            if 'series_name' in named_groups:
                result.series_name = match.group('series_name')
                if result.series_name:
                    result.series_name = self.clean_series_name(result.series_name)
                    result.score += 1

            if 'series_num' in named_groups and match.group('series_num'):
                result.score += 1

            if 'season_num' in named_groups:
                tmp_season = int(match.group('season_num'))
                if cur_regex_name == 'bare' and tmp_season in (19, 20):
                    continue
                if cur_regex_name == 'fov' and tmp_season > 500:
                    continue

                result.season_number = tmp_season
                result.score += 1

            if 'ep_num' in named_groups:
                ep_num = self._convert_number(match.group('ep_num'))
                if 'extra_ep_num' in named_groups and match.group('extra_ep_num'):
                    tmp_episodes = range(ep_num, self._convert_number(match.group('extra_ep_num')) + 1)
                    if len(tmp_episodes) > 4:
                        matches = []
                        break
                else:
                    tmp_episodes = [ep_num]

                result.episode_numbers = tmp_episodes
                result.score += 3

            if 'ep_ab_num' in named_groups:
                ep_ab_num = self._convert_number(match.group('ep_ab_num'))
                if 'extra_ab_ep_num' in named_groups and match.group('extra_ab_ep_num'):
                    result.ab_episode_numbers = range(ep_ab_num,
                                                      self._convert_number(match.group('extra_ab_ep_num')) + 1)
                    result.score += 1
                else:
                    result.ab_episode_numbers = [ep_ab_num]
                result.score += 1

            if 'air_date' in named_groups:
                air_date = match.group('air_date')
                try:
                    assert re.sub(r'[^\d]*', '', air_date) != '112263'
                    result.air_date = dateutil.parser.parse(air_date, fuzzy_with_tokens=True)[0].date()
                    result.score += 1
                except Exception:
                    continue

            if 'extra_info' in named_groups:
                tmp_extra_info = match.group('extra_info')

                # Show.S04.Special or Show.S05.Part.2.Extras is almost certainly not every episode in the season
                if tmp_extra_info and cur_regex_name == 'season_only' and re.search(
                        r'([. _-]|^)(special|extra)s?\w*([. _-]|$)', tmp_extra_info, re.I):
                    continue
                result.extra_info = tmp_extra_info
                result.score += 1

            if 'release_group' in named_groups:
                result.release_group = match.group('release_group')
                result.score += 1

            if 'version' in named_groups:
                # assigns version to anime file if detected using anime regex. Non-anime regex receives -1
                version = match.group('version')
                if version:
                    result.version = version
                else:
                    result.version = 1
            else:
                result.version = -1

            matches.append(result)

        if matches:
            # pick best match with highest score based on placement
            bestResult = max(sorted(matches, reverse=True, key=lambda x: x.which_regex), key=lambda x: x.score)

            show = None
            if not self.naming_pattern:
                # try and create a show object for this result
                show = helpers.get_show(bestResult.series_name, self.tryIndexers)

            # confirm passed in show object indexer id matches result show object indexer id
            if show:
                if self.showObj and show.indexerid != self.showObj.indexerid:
                    show = None
                bestResult.show = show
            elif not show and self.showObj:
                bestResult.show = self.showObj

            # if this is a naming pattern test or result doesn't have a show object then return best result
            if not bestResult.show or self.naming_pattern:
                return bestResult

            # get quality
            bestResult.quality = common.Quality.nameQuality(name, bestResult.show.is_anime)

            new_episode_numbers = []
            new_season_numbers = []
            new_absolute_numbers = []

            # if we have an air-by-date show then get the real season/episode numbers
            if bestResult.is_air_by_date:
                airdate = bestResult.air_date.toordinal()
                main_db_con = db.DBConnection()
                sql_result = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                    [bestResult.show.indexerid, bestResult.show.indexer, airdate])

                season_number = None
                episode_numbers = []

                if sql_result:
                    season_number = int(sql_result[0][0])
                    episode_numbers = [int(sql_result[0][1])]

                if season_number is None or not episode_numbers:
                    try:
                        lINDEXER_API_PARMS = sickbeard.indexerApi(bestResult.show.indexer).api_params.copy()

                        lINDEXER_API_PARMS['language'] = bestResult.show.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

                        t = sickbeard.indexerApi(bestResult.show.indexer).indexer(**lINDEXER_API_PARMS)

                        epObj = t[bestResult.show.indexerid].airedOn(bestResult.air_date)[0]

                        season_number = int(epObj["seasonnumber"])
                        episode_numbers = [int(epObj["episodenumber"])]
                    except sickbeard.indexer_episodenotfound:
                        logger.log("Unable to find episode with date " + six.text_type(bestResult.air_date) + " for show " + bestResult.show.name + ", skipping", logger.WARNING)
                        episode_numbers = []
                    except sickbeard.indexer_error as e:
                        logger.log("Unable to contact " + sickbeard.indexerApi(bestResult.show.indexer).name + ": " + ex(e), logger.WARNING)
                        episode_numbers = []

                for epNo in episode_numbers:
                    s = season_number
                    e = epNo

                    if bestResult.show.is_scene:
                        (s, e) = scene_numbering.get_indexer_numbering(bestResult.show.indexerid,
                                                                       bestResult.show.indexer,
                                                                       season_number,
                                                                       epNo)
                    new_episode_numbers.append(e)
                    new_season_numbers.append(s)

            elif bestResult.show.is_anime and bestResult.ab_episode_numbers:
                bestResult.scene_season = scene_exceptions.get_scene_exception_by_name(bestResult.series_name)[1]
                for epAbsNo in bestResult.ab_episode_numbers:
                    a = epAbsNo

                    if bestResult.show.is_scene and not skip_scene_detection:
                        a = scene_numbering.get_indexer_absolute_numbering(bestResult.show.indexerid,
                                                                           bestResult.show.indexer, epAbsNo,
                                                                           True, bestResult.scene_season)

                    (s, e) = helpers.get_all_episodes_from_absolute_number(bestResult.show, [a])

                    new_absolute_numbers.append(a)
                    new_episode_numbers.extend(e)
                    new_season_numbers.append(s)

            elif bestResult.season_number and bestResult.episode_numbers:
                for epNo in bestResult.episode_numbers:
                    s = bestResult.season_number
                    e = epNo

                    if bestResult.show.is_scene and not skip_scene_detection:
                        (s, e) = scene_numbering.get_indexer_numbering(bestResult.show.indexerid,
                                                                       bestResult.show.indexer,
                                                                       bestResult.season_number,
                                                                       epNo)
                    if bestResult.show.is_anime:
                        a = helpers.get_absolute_number_from_season_and_episode(bestResult.show, s, e)
                        if a:
                            new_absolute_numbers.append(a)

                    new_episode_numbers.append(e)
                    new_season_numbers.append(s)

            # need to do a quick sanity check heregex.  It's possible that we now have episodes
            # from more than one season (by tvdb numbering), and this is just too much
            # for sickbeard, so we'd need to flag it.
            new_season_numbers = list(set(new_season_numbers))  # remove duplicates
            if len(new_season_numbers) > 1:
                raise InvalidNameException("Scene numbering results episodes from "
                                           "seasons %s, (i.e. more than one) and "
                                           "sickrage does not support this.  "
                                           "Sorry." % (six.text_type(new_season_numbers)))

            # I guess it's possible that we'd have duplicate episodes too, so lets
            # eliminate them
            new_episode_numbers = list(set(new_episode_numbers))
            new_episode_numbers.sort()

            # maybe even duplicate absolute numbers so why not do them as well
            new_absolute_numbers = list(set(new_absolute_numbers))
            new_absolute_numbers.sort()

            if new_absolute_numbers:
                bestResult.ab_episode_numbers = new_absolute_numbers

            if new_season_numbers and new_episode_numbers:
                bestResult.episode_numbers = new_episode_numbers
                bestResult.season_number = new_season_numbers[0]

            if bestResult.show.is_scene and not skip_scene_detection:
                logger.log(
                    "Converted parsed result " + bestResult.original_name + " into " + six.text_type(bestResult), logger.DEBUG)

        # CPU sleep
        time.sleep(0.02)

        return bestResult

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
            obj = six.text_type(obj, encoding, 'replace')
        return obj

    @staticmethod
    def _convert_number(org_number):
        """
         Convert org_number into an integer
         org_number: integer or representation of a number: string or six.text_type
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
                ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100),
                ('XC', 90), ('L', 50), ('XL', 40), ('X', 10),
                ('IX', 9), ('V', 5), ('IV', 4), ('I', 1)
            )

            roman_numeral = six.text_type(org_number).upper()
            number = 0
            index = 0

            for numeral, integer in roman_to_int_map:
                while roman_numeral[index:index + len(numeral)] == numeral:
                    number += integer
                    index += len(numeral)

        return number

    def parse(self, name, cache_result=True, skip_scene_detection=False):
        name = self._unicodify(name)

        if self.naming_pattern:
            cache_result = False

        cached = name_parser_cache.get(name)
        if cached:
            return cached

        # break it into parts if there are any (dirname, file name, extension)
        dir_name, file_name = ek(os.path.split, name)

        if self.file_name:
            base_file_name = remove_extension(file_name)
        else:
            base_file_name = file_name

        # set up a result to use
        final_result = ParseResult(name)

        # try parsing the file name
        file_name_result = self._parse_string(base_file_name, skip_scene_detection)

        # use only the direct parent dir
        dir_name = ek(os.path.basename, dir_name)

        # parse the dirname for extra info if needed
        dir_name_result = self._parse_string(dir_name, skip_scene_detection)

        # build the ParseResult object
        final_result.air_date = self._combine_results(file_name_result, dir_name_result, 'air_date')

        # anime absolute numbers
        final_result.ab_episode_numbers = self._combine_results(file_name_result, dir_name_result, 'ab_episode_numbers')

        # season and episode numbers
        final_result.season_number = self._combine_results(file_name_result, dir_name_result, 'season_number')
        final_result.episode_numbers = self._combine_results(file_name_result, dir_name_result, 'episode_numbers')
        final_result.scene_season = self._combine_results(file_name_result, dir_name_result, 'scene_season')

        # if the dirname has a release group/show name I believe it over the filename
        final_result.series_name = self._combine_results(dir_name_result, file_name_result, 'series_name')
        final_result.extra_info = self._combine_results(dir_name_result, file_name_result, 'extra_info')
        final_result.release_group = self._combine_results(dir_name_result, file_name_result, 'release_group')
        final_result.version = self._combine_results(dir_name_result, file_name_result, 'version')

        final_result.which_regex = []
        if final_result == file_name_result:
            final_result.which_regex = file_name_result.which_regex
        elif final_result == dir_name_result:
            final_result.which_regex = dir_name_result.which_regex
        else:
            if file_name_result:
                final_result.which_regex += file_name_result.which_regex
            if dir_name_result:
                final_result.which_regex += dir_name_result.which_regex

        final_result.show = self._combine_results(file_name_result, dir_name_result, 'show')
        final_result.quality = self._combine_results(file_name_result, dir_name_result, 'quality')

        if not final_result.show:
            raise InvalidShowException("Unable to match {0} to a show in your database. Parser result: {1}".format(
                name, six.text_type(final_result))

        # if there's no useful info in it then raise an exception
        if final_result.season_number is None and not final_result.episode_numbers and final_result.air_date is None and not final_result.ab_episode_numbers and not final_result.series_name:
            raise InvalidNameException("Unable to parse {0} to a valid episode of {1}. Parser result: {2}".format(
                name, final_result.show.name, six.text_type(final_result))

        if cache_result:
            name_parser_cache.add(name, final_result)

        logger.log("Parsed " + name + " into " + six.text_type(final_result), logger.DEBUG)
        return final_result


class ParseResult(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self, original_name, series_name=None, season_number=None,  # pylint: disable=too-many-arguments
                 episode_numbers=None, extra_info=None, release_group=None,
                 air_date=None, ab_episode_numbers=None, show=None,
                 score=None, quality=None, version=None):

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
        self.show = show
        self.score = score

        self.version = version

        self.scene_season = None

    def __eq__(self, other):
        return other and all([
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
            self.version == other.version
        ])

    def __unicode__(self):
        if self.series_name is not None:
            to_return = self.series_name + ' - '
        else:
            to_return = ''
        if self.season_number is not None:
            to_return += 'S' + six.text_type(self.season_number).zfill(2)
        if self.episode_numbers:
            for e in self.episode_numbers:
                to_return += 'E' + six.text_type(e).zfill(2)

        if self.is_air_by_date:
            to_return += six.text_type(self.air_date)
        if self.ab_episode_numbers:
            to_return += ' [ABS: ' + six.text_type(self.ab_episode_numbers) + ']'
        if self.version and self.is_anime is True:
            to_return += ' [ANIME VER: ' + six.text_type(self.version) + ']'

        if self.release_group:
            to_return += ' [GROUP: ' + self.release_group + ']'

        to_return += ' [ABD: ' + six.text_type(self.is_air_by_date) + ']'
        to_return += ' [ANIME: ' + six.text_type(self.is_anime) + ']'
        to_return += ' [whichReg: ' + six.text_type(self.which_regex) + ']'

        return to_return

    def __str__(self):
        return self.__unicode__().encode('utf-8', errors='replace')

    @property
    def is_air_by_date(self):
        if self.air_date:
            return True
        return False

    @property
    def is_anime(self):
        if self.ab_episode_numbers:
            return True
        return False


class NameParserCache(object):

    def __init__(self):
        self.lock = Lock()
        self.data = OrderedDict()
        self.max_size = 200

    def get(self, key):
        with self.lock:
            value = self.data.get(key, None)
            if value:
                logger.log("Using cached parse result for: {name}".format(name=key), logger.DEBUG)
            return value

    def add(self, key, value):
        with self.lock:
            self.data.update({key: value})
            while len(self.data) > self.max_size:
                self.data.pop(list(self.data.keys())[0], None)

name_parser_cache = NameParserCache()


class InvalidNameException(Exception):
    """The given release name is not valid"""


class InvalidShowException(Exception):
    """The given show name is not valid"""
