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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os.path
import re
import threading
import regexes
import time
import sickbeard

from sickbeard import logger, helpers, scene_numbering, db
from sickbeard.exceptions import EpisodeNotFoundByAbsoluteNumberException
from dateutil import parser

nameparser_lock = threading.Lock()


class NameParser(object):
    ALL_REGEX = 0
    NORMAL_REGEX = 1
    SPORTS_REGEX = 2
    ANIME_REGEX = 3

    def __init__(self, file_name=True, show=None, useIndexers=False):

        regexMode = self.ALL_REGEX
        if show and show.is_anime:
            regexMode = self.ANIME_REGEX
        elif show and show.is_sports:
            regexMode = self.SPORTS_REGEX
        elif show and not show.is_anime and not show.is_sports:
            regexMode = self.NORMAL_REGEX

        self.file_name = file_name
        self.regexMode = regexMode
        self.compiled_regexes = {}
        self._compile_regexes(self.regexMode)
        self.showList = sickbeard.showList
        self.useIndexers = useIndexers
        self.show = show

    def clean_series_name(self, series_name):
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

        series_name = re.sub("(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub("(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub("(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub("\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub("-$", "", series_name)
        series_name = re.sub("^\[.*\]", "", series_name)
        return series_name.strip()

    def _compile_regexes(self, regexMode):
        if regexMode <= self.ALL_REGEX:
            logger.log(u"Using ALL regexs", logger.DEBUG)
            uncompiled_regex = [regexes.anime_regexes, regexes.sports_regexs, regexes.normal_regexes]

        elif regexMode == self.NORMAL_REGEX:
            logger.log(u"Using NORMAL regexs", logger.DEBUG)
            uncompiled_regex = [regexes.normal_regexes]

        elif regexMode == self.SPORTS_REGEX:
            logger.log(u"Using SPORTS regexs", logger.DEBUG)
            uncompiled_regex = [regexes.sports_regexs]

        elif regexMode == self.ANIME_REGEX:
            logger.log(u"Using ANIME regexs", logger.DEBUG)
            uncompiled_regex = [regexes.anime_regexes, regexes.normal_regexes]

        else:
            logger.log(u"This is a programing ERROR. Fallback Using NORMAL regexs", logger.ERROR)
            uncompiled_regex = [regexes.normal_regexes]

        for regexItem in uncompiled_regex:
            for regex_type, regex in regexItem.items():
                try:
                    self.compiled_regexes[regex_type]
                except:
                    self.compiled_regexes[regex_type] = {}

                for (cur_pattern_name, cur_pattern) in regex:
                    try:
                        cur_regex = re.compile(cur_pattern, re.VERBOSE | re.IGNORECASE)
                    except re.error, errormsg:
                        logger.log(u"WARNING: Invalid episode_pattern, %s. %s" % (errormsg, cur_pattern))
                    else:
                        self.compiled_regexes[regex_type].update({cur_pattern_name: cur_regex})

    def _parse_string(self, name):
        for cur_regex_type, cur_regexes in self.compiled_regexes.items() if name else []:
            for cur_regex_name, cur_regex in cur_regexes.items():
                match = cur_regex.match(name)

                if not match:
                    continue

                result = ParseResult(name)
                result.which_regex = [cur_regex_name]

                named_groups = match.groupdict().keys()

                if 'series_name' in named_groups:
                    result.series_name = match.group('series_name')
                    if result.series_name:
                        result.series_name = self.clean_series_name(result.series_name)

                if 'season_num' in named_groups:
                    tmp_season = int(match.group('season_num'))
                    if cur_regex_name == 'bare' and tmp_season in (19, 20):
                        continue
                    result.season_number = tmp_season

                if 'ep_num' in named_groups:
                    ep_num = self._convert_number(match.group('ep_num'))
                    if 'extra_ep_num' in named_groups and match.group('extra_ep_num'):
                        result.episode_numbers = range(ep_num, self._convert_number(match.group('extra_ep_num')) + 1)
                    else:
                        result.episode_numbers = [ep_num]

                if 'ep_ab_num' in named_groups:
                    ep_ab_num = self._convert_number(match.group('ep_ab_num'))
                    if 'extra_ab_ep_num' in named_groups and match.group('extra_ab_ep_num'):
                        result.ab_episode_numbers = range(ep_ab_num,
                                                          self._convert_number(match.group('extra_ab_ep_num')) + 1)
                    else:
                        result.ab_episode_numbers = [ep_ab_num]

                if 'sports_event_id' in named_groups:
                    sports_event_id = match.group('sports_event_id')
                    if sports_event_id:
                        result.sports_event_id = int(match.group('sports_event_id'))

                if 'sports_event_name' in named_groups:
                    result.sports_event_name = match.group('sports_event_name')
                    if result.sports_event_name:
                        result.sports_event_name = self.clean_series_name(result.sports_event_name)

                if 'sports_event_date' in named_groups:
                    sports_event_date = match.group('sports_event_date')
                    if sports_event_date:
                        try:
                            result.sports_event_date = parser.parse(sports_event_date, fuzzy=True).date()
                        except:
                            continue

                if 'air_year' in named_groups and 'air_month' in named_groups and 'air_day' in named_groups:
                    year = int(match.group('air_year'))
                    month = int(match.group('air_month'))
                    day = int(match.group('air_day'))

                    try:
                        dtStr = '%s-%s-%s' % (year, month, day)
                        result.air_date = datetime.datetime.strptime(dtStr, "%Y-%m-%d").date()
                    except:
                        continue

                if 'extra_info' in named_groups:
                    tmp_extra_info = match.group('extra_info')

                    # Show.S04.Special or Show.S05.Part.2.Extras is almost certainly not every episode in the season
                    if tmp_extra_info and cur_regex_name == 'season_only' and re.search(
                            r'([. _-]|^)(special|extra)s?\w*([. _-]|$)', tmp_extra_info, re.I):
                        continue
                    result.extra_info = tmp_extra_info

                if 'release_group' in named_groups:
                    result.release_group = match.group('release_group')

                # determin show object for correct regex matching
                if not self.show:
                    show = helpers.get_show_by_name(result.series_name, useIndexer=self.useIndexers)
                else:
                    show = self.show

                if show and show.is_anime and cur_regex_type in ['anime', 'normal']:
                    result.show = show
                    return result
                elif show and show.is_sports and cur_regex_type == 'sports':
                    result.show = show
                    return result
                elif cur_regex_type == 'normal':
                    result.show = show if show else None
                    return result

        return None

    def _combine_results(self, first, second, attr):
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
        if a != None or (type(a) == list and len(a)):
            return a
        # if not use b (if b isn't set it'll just be default)
        else:
            return b

    def _unicodify(self, obj, encoding="utf-8"):
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    def _convert_number(self, number):

        try:
            return int(number)
        except:
            numeral_map = zip(
                (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
                ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
            )

            n = unicode(number).upper()

            i = result = 0
            for integer, numeral in numeral_map:
                while n[i:i + len(numeral)] == numeral:
                    result += integer
                    i += len(numeral)

            return result

    def parse(self, name, cache_result=True):
        name = self._unicodify(name)

        cached = name_parser_cache.get(name)
        if cached:
            return cached

        # break it into parts if there are any (dirname, file name, extension)
        dir_name, file_name = os.path.split(name)
        ext_match = re.match('(.*)\.\w{3,4}$', file_name)
        if ext_match and self.file_name:
            base_file_name = ext_match.group(1)
        else:
            base_file_name = file_name

        # use only the direct parent dir
        dir_name = os.path.basename(dir_name)

        # set up a result to use
        final_result = ParseResult(name)

        # try parsing the file name
        file_name_result = self._parse_string(base_file_name)

        # parse the dirname for extra info if needed
        dir_name_result = self._parse_string(dir_name)

        # build the ParseResult object
        final_result.air_date = self._combine_results(file_name_result, dir_name_result, 'air_date')
        final_result.ab_episode_numbers = self._combine_results(file_name_result, dir_name_result, 'ab_episode_numbers')

        # sports event title
        final_result.sports_event_id = self._combine_results(file_name_result, dir_name_result, 'sports_event_id')
        final_result.sports_event_name = self._combine_results(file_name_result, dir_name_result, 'sports_event_name')
        final_result.sports_event_date = self._combine_results(file_name_result, dir_name_result, 'sports_event_date')

        if not final_result.air_date:
            final_result.season_number = self._combine_results(file_name_result, dir_name_result, 'season_number')
            final_result.episode_numbers = self._combine_results(file_name_result, dir_name_result, 'episode_numbers')

        # if the dirname has a release group/show name I believe it over the filename
        final_result.series_name = self._combine_results(dir_name_result, file_name_result, 'series_name')

        final_result.extra_info = self._combine_results(dir_name_result, file_name_result, 'extra_info')
        final_result.release_group = self._combine_results(dir_name_result, file_name_result, 'release_group')

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
        if final_result.show and final_result.show.is_anime and final_result.is_anime:  # only need to to do another conversion if the scene2tvdb didn work
            logger.log("Getting season and episodes from absolute numbers", logger.DEBUG)
            try:
                _actual_season, _actual_episodes = helpers.get_all_episodes_from_absolute_number(final_result.show,
                                                                                                 None,
                                                                                                 final_result.ab_episode_numbers)
            except EpisodeNotFoundByAbsoluteNumberException:
                logger.log(str(final_result.show.indexerid) + ": Indexer object absolute number " + str(
                    final_result.ab_episode_numbers) + " is incomplete, cant determin season and episode numbers")
            else:
                final_result.season = _actual_season
                final_result.episodes = _actual_episodes

        # if there's no useful info in it then raise an exception
        if final_result.season_number == None and not final_result.episode_numbers and final_result.air_date == None and not final_result.series_name:
            raise InvalidNameException("Unable to parse " + name.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))

        if cache_result:
            name_parser_cache.add(name, final_result)

        return final_result


    def scene2indexer(self, show, scene_name, season, episodes, absolute_numbers):
        if not show: return self  # need show object

        # TODO: check if adb and make scene2indexer useable with correct numbers
        out_season = None
        out_episodes = []
        out_absolute_numbers = []

        # is the scene name a special season ?
        # TODO: define if we get scene seasons or indexer seasons ... for now they are mostly the same ... and i will use them as scene seasons
        _possible_seasons = sickbeard.scene_exceptions.get_scene_exception_by_name_multiple(scene_name)
        # filter possible_seasons
        possible_seasons = []
        for cur_scene_indexer_id, cur_scene_season in _possible_seasons:
            if cur_scene_indexer_id and str(cur_scene_indexer_id) != str(show.indexerid):
                logger.log("Indexer ID mismatch: " + str(show.indexerid) + " now: " + str(cur_scene_indexer_id),
                           logger.ERROR)
                raise MultipleSceneShowResults("indexerid mismatch")
            # don't add season -1 since this is a generic name and not a real season... or if we get None
            # if this was the only result possible_seasons will stay empty and the next parts will look in the general matter
            if cur_scene_season == -1 or cur_scene_season == None:
                continue
            possible_seasons.append(cur_scene_season)
        # if not possible_seasons: # no special season name was used or we could not find it
        logger.log(
            "possible seasons for '" + scene_name + "' (" + str(show.indexerid) + ") are " + str(possible_seasons),
            logger.DEBUG)

        # lets just get a db connection we will need it anyway
        cacheDB = db.DBConnection('cache.db')
        # should we use absolute_numbers -> anime or season, episodes -> normal show
        if show.is_anime:
            logger.log(
                u"'" + show.name + "' is an anime i will scene convert the absolute numbers " + str(absolute_numbers),
                logger.DEBUG)
            if possible_seasons:
                # check if we have a scene_absolute_number in the possible seasons
                for cur_possible_season in possible_seasons:
                    # and for all absolute numbers
                    for cur_ab_number in absolute_numbers:
                        namesSQlResult = cacheDB.select(
                            "SELECT season, episode, absolute_number FROM xem_numbering WHERE indexer_id = ? and scene_season = ? and scene_absolute_number = ?",
                            [show.indexerid, cur_possible_season, cur_ab_number])
                        if len(namesSQlResult) > 1:
                            logger.log(
                                "Multiple episodes for a absolute number and season. check XEM numbering",
                                logger.ERROR)
                            raise MultipleSceneEpisodeResults("Multiple episodes for a absolute number and season")
                        elif len(namesSQlResult) == 0:
                            break  # break out of current absolute_numbers -> next season ... this is not a good sign
                        # if we are here we found ONE episode for this season absolute number
                        # logger.log(u"I found matching episode: " + namesSQlResult[0]['name'], logger.DEBUG)
                        out_episodes.append(int(namesSQlResult[0]['episode']))
                        out_absolute_numbers.append(int(namesSQlResult[0]['absolute_number']))
                        out_season = int(namesSQlResult[0][
                            'season'])  # note this will always use the last season we got ... this will be a problem on double episodes that break the season barrier
                    if out_season:  # if we found a episode in the cur_possible_season we dont need / want to look at the other season possibilities
                        break
            else:  # no possible seasons from the scene names lets look at this more generic
                for cur_ab_number in absolute_numbers:
                    namesSQlResult = cacheDB.select(
                        "SELECT season, episode, absolute_number FROM xem_numbering WHERE indexer_id = ? and scene_absolute_number = ?",
                        [show.indexerid, cur_ab_number])
                    if len(namesSQlResult) > 1:
                        logger.log(
                            "Multiple episodes for a absolute number. this might happend because we are missing a scene name for this season. xem lacking behind ?",
                            logger.ERROR)
                        raise MultipleSceneEpisodeResults("Multiple episodes for a absolute number")
                    elif len(namesSQlResult) == 0:
                        continue
                    # if we are here we found ONE episode for this season absolute number
                    # logger.log(u"I found matching episode: " + namesSQlResult[0]['name'], logger.DEBUG)
                    out_episodes.append(int(namesSQlResult[0]['episode']))
                    out_absolute_numbers.append(int(namesSQlResult[0]['absolute_number']))
                    out_season = int(namesSQlResult[0][
                        'season'])  # note this will always use the last season we got ... this will be a problem on double episodes that break the season barrier
            if not out_season:  # we did not find anything in the loops ? damit there is no episode
                logger.log("No episode found for these scene numbers. asuming indexer numbers", logger.DEBUG)
                # we still have to convert the absolute number to sxxexx ... but that is done not here
        else:
            logger.log(u"'" + show.name + "' is a normal show i will scene convert the season and episodes " + str(
                season) + "x" + str(episodes), logger.DEBUG)
            out_absolute_numbers = None
            if possible_seasons:
                # check if we have a scene_absolute_number in the possible seasons
                for cur_possible_season in possible_seasons:
                    # and for all episode
                    for cur_episode in episodes:
                        namesSQlResult = cacheDB.select(
                            "SELECT season, episode FROM xem_numbering WHERE indexer_id = ? and scene_season = ? and scene_episode = ?",
                            [show.indexerid, cur_possible_season, cur_episode])
                        if len(namesSQlResult) > 1:
                            logger.log(
                                "Multiple episodes for season episode number combination. this should not be check xem configuration",
                                logger.ERROR)
                            raise MultipleSceneEpisodeResults("Multiple episodes for season episode number combination")
                        elif len(namesSQlResult) == 0:
                            break  # break out of current episode -> next season ... this is not a good sign
                        # if we are here we found ONE episode for this season absolute number
                        # logger.log(u"I found matching episode: " + namesSQlResult[0]['name'], logger.DEBUG)
                        out_episodes.append(int(namesSQlResult[0]['episode']))
                        out_season = int(namesSQlResult[0][
                            'season'])  # note this will always use the last season we got ... this will be a problem on double episodes that break the season barrier
                    if out_season:  # if we found a episode in the cur_possible_season we dont need / want to look at the other posibilites
                        break
            else:  # no possible seasons from the scene names lets look at this more generic
                for cur_episode in episodes:
                    namesSQlResult = cacheDB.select(
                        "SELECT season, episode FROM xem_numbering WHERE indexer_id = ? and scene_episode = ? and scene_season = ?",
                        [show.indexerid, cur_episode, season])
                    if len(namesSQlResult) > 1:
                        logger.log(
                            "Multiple episodes for season episode number combination. this might happend because we are missing a scene name for this season. xem lacking behind ?",
                            logger.ERROR)
                        raise MultipleSceneEpisodeResults("Multiple episodes for season episode number combination")
                    elif len(namesSQlResult) == 0:
                        continue
                    # if we are here we found ONE episode for this season absolute number
                    # logger.log(u"I found matching episode: " + namesSQlResult[0]['name'], logger.DEBUG)
                    out_episodes.append(int(namesSQlResult[0]['episode']))
                    out_season = int(namesSQlResult[0][
                        'season'])  # note this will always use the last season we got ... this will be a problem on double episodes that break the season barrier
            # this is only done for normal shows
            if not out_season:  # we did not find anything in the loops ? darn there is no episode
                logger.log("No episode found for these scene numbers. assuming these are valid indexer numbers",
                           logger.DEBUG)
                out_season = season
                out_episodes = episodes
                out_absolute_numbers = absolute_numbers

        # okay that was easy we found the correct season and episode numbers
        return (out_season, out_episodes, out_absolute_numbers)


class ParseResult(object):
    def __init__(self,
                 original_name,
                 series_name=None,
                 sports_event_id=None,
                 sports_event_name=None,
                 sports_event_date=None,
                 season_number=None,
                 episode_numbers=None,
                 extra_info=None,
                 release_group=None,
                 air_date=None,
                 ab_episode_numbers=None,
                 show=None
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

        self.extra_info = extra_info
        self.release_group = release_group

        self.air_date = air_date

        self.sports_event_id = sports_event_id
        self.sports_event_name = sports_event_name
        self.sports_event_date = sports_event_date

        self.which_regex = None
        self.show = show

    def __eq__(self, other):
        if not other:
            return False

        if self.series_name != other.series_name:
            return False
        if self.season_number != other.season_number:
            return False
        if self.episode_numbers != other.episode_numbers:
            return False
        if self.extra_info != other.extra_info:
            return False
        if self.release_group != other.release_group:
            return False
        if self.air_date != other.air_date:
            return False
        if self.sports_event_id != other.sports_event_id:
            return False
        if self.sports_event_name != other.sports_event_name:
            return False
        if self.sports_event_date != other.sports_event_date:
            return False
        if self.ab_episode_numbers != other.ab_episode_numbers:
            return False
        if self.show != other.show:
            return False

        return True

    def __str__(self):
        if self.series_name != None:
            to_return = self.series_name + u' - '
        else:
            to_return = u''
        if self.season_number != None:
            to_return += 'S' + str(self.season_number)
        if self.episode_numbers and len(self.episode_numbers):
            for e in self.episode_numbers:
                to_return += 'E' + str(e)

        if self.air_by_date:
            to_return += str(self.air_date)
        if self.sports:
            to_return += str(self.sports_event_name)
            to_return += str(self.sports_event_id)
            to_return += str(self.sports_event_date)
        if self.ab_episode_numbers:
            to_return += ' absolute_numbers: ' + str(self.ab_episode_numbers)

        if self.extra_info:
            to_return += ' - ' + self.extra_info
        if self.release_group:
            to_return += ' (' + self.release_group + ')'

        to_return += ' [ABD: ' + str(self.air_by_date) + ']'
        to_return += ' [SPORTS: ' + str(self.sports) + ']'
        to_return += ' [ANIME: ' + str(self.is_anime) + ']'
        to_return += ' [whichReg: ' + str(self.which_regex) + ']'

        return to_return.encode('utf-8')

    def convert(self):
        if not self.show: return self  # need show object
        if not self.season_number: return self  # can't work without a season
        if not len(self.episode_numbers): return self  # need at least one episode
        if self.air_by_date or self.sports: return self  # scene numbering does not apply to air-by-date

        new_episode_numbers = []
        new_season_numbers = []
        new_absolute_numbers = []

        for i, epNo in enumerate(self.episode_numbers):
            abNo = None
            if len(self.ab_episode_numbers):
                abNo = self.ab_episode_numbers[i]

            (s, e, a) = scene_numbering.get_indexer_numbering(self.show.indexerid, self.show.indexer,
                                                              self.season_number,
                                                              epNo, abNo)
            new_episode_numbers.append(e)
            new_season_numbers.append(s)
            new_absolute_numbers.append(a)

        # need to do a quick sanity check here.  It's possible that we now have episodes
        # from more than one season (by tvdb numbering), and this is just too much
        # for sickbeard, so we'd need to flag it.
        new_season_numbers = list(set(new_season_numbers))  # remove duplicates
        if len(new_season_numbers) > 1:
            raise InvalidNameException("Scene numbering results episodes from "
                                       "seasons %s, (i.e. more than one) and "
                                       "sickrage does not support this.  "
                                       "Sorry." % (str(new_season_numbers)))

        # I guess it's possible that we'd have duplicate episodes too, so lets
        # eliminate them
        new_episode_numbers = list(set(new_episode_numbers))
        new_episode_numbers.sort()

        # dedupe absolute numbers
        new_absolute_numbers = list(set(new_absolute_numbers))
        new_absolute_numbers.sort()

        self.ab_episode_numbers = new_absolute_numbers
        self.episode_numbers = new_episode_numbers
        self.season_number = new_season_numbers[0]

        return self

    def _is_air_by_date(self):
        if self.season_number == None and len(self.episode_numbers) == 0 and self.air_date:
            return True
        return False

    air_by_date = property(_is_air_by_date)

    def _is_anime(self):
        if self.ab_episode_numbers:
            if self.show and self.show.is_anime:
                return True
        return False

    is_anime = property(_is_anime)

    def _is_sports(self):
        if self.sports_event_date:
            return True
        return False

    sports = property(_is_sports)


class NameParserCache(object):
    _previous_parsed = {}
    _cache_size = 100

    def add(self, name, parse_result):
        self._previous_parsed[name] = parse_result
        _current_cache_size = len(self._previous_parsed)
        if _current_cache_size > self._cache_size:
            for i in range(_current_cache_size - self._cache_size):
                del self._previous_parsed[self._previous_parsed.keys()[0]]

    def get(self, name):
        if name in self._previous_parsed:
            logger.log("Using cached parse result for: " + name, logger.DEBUG)
            return self._previous_parsed[name]


name_parser_cache = NameParserCache()


class InvalidNameException(Exception):
    "The given name is not valid"


class MultipleSceneShowResults(Exception):
    pass


class MultipleSceneEpisodeResults(Exception):
    pass
