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

import fnmatch
import os

import re
import datetime
from functools import partial

import sickbeard
from sickbeard import common
from sickbeard.helpers import sanitizeSceneName
from sickbeard.scene_exceptions import get_scene_exceptions
from sickbeard import logger
from sickbeard import db
from sickrage.helper.encoding import ek, ss
from name_parser.parser import NameParser, InvalidNameException, InvalidShowException

resultFilters = [
    "sub(bed|ed|pack|s)",
    "(dk|fin|heb|kor|nor|nordic|pl|swe)sub(bed|ed|s)?",
    "(dir|sample|sub|nfo)fix",
    "sample",
    "(dvd)?extras",
    "dub(bed)?"
]


def containsAtLeastOneWord(name, words):
    """
    Filters out results based on filter_words

    name: name to check
    words : string of words separated by a ',' or list of words

    Returns: False if the name doesn't contain any word of words list, or the found word from the list.
    """
    if isinstance(words, basestring):
        words = words.split(',')
    items = [(re.compile('(^|[\W_])%s($|[\W_])' % re.escape(word.strip()), re.I), word.strip()) for word in words]
    for regexp, word in items:
        if regexp.search(name):
            return word
    return False


def filterBadReleases(name, parse=True):
    """
    Filters out non-english and just all-around stupid releases by comparing them
    to the resultFilters contents.

    name: the release name to check

    Returns: True if the release name is OK, False if it's bad.
    """

    try:
        if parse:
            NameParser().parse(name)
    except InvalidNameException:
        logger.log(u"Unable to parse the filename " + name + " into a valid episode", logger.DEBUG)
        return False
    except InvalidShowException:
        pass
    #    logger.log(u"Unable to parse the filename " + name + " into a valid show", logger.DEBUG)
    #    return False

    # if any of the bad strings are in the name then say no
    ignore_words = list(resultFilters)
    if sickbeard.IGNORE_WORDS:
        ignore_words.extend(sickbeard.IGNORE_WORDS.split(','))
    word = containsAtLeastOneWord(name, ignore_words)
    if word:
        logger.log(u"Invalid scene release: " + name + " contains " + word + ", ignoring it", logger.DEBUG)
        return False

    # if any of the good strings aren't in the name then say no
    if sickbeard.REQUIRE_WORDS:
        require_words = sickbeard.REQUIRE_WORDS
        if not containsAtLeastOneWord(name, require_words):
            logger.log(u"Invalid scene release: " + name + " doesn't contain any of " + sickbeard.REQUIRE_WORDS +
                       ", ignoring it", logger.DEBUG)
            return False

    return True


def sceneToNormalShowNames(name):
    """
        Takes a show name from a scene dirname and converts it to a more "human-readable" format.

    name: The show name to convert

    Returns: a list of all the possible "normal" names
    """

    if not name:
        return []

    name_list = [name]

    # use both and and &
    new_name = re.sub('(?i)([\. ])and([\. ])', '\\1&\\2', name, re.I)
    if new_name not in name_list:
        name_list.append(new_name)

    results = []

    for cur_name in name_list:
        # add brackets around the year
        results.append(re.sub('(\D)(\d{4})$', '\\1(\\2)', cur_name))

        # add brackets around the country
        country_match_str = '|'.join(common.countryList.values())
        results.append(re.sub('(?i)([. _-])(' + country_match_str + ')$', '\\1(\\2)', cur_name))

    results += name_list

    return list(set(results))


def makeSceneShowSearchStrings(show, season=-1, anime=False):
    showNames = allPossibleShowNames(show, season=season)

    # scenify the names
    if anime:
        sanitizeSceneNameAnime = partial(sanitizeSceneName, anime=True)
        return map(sanitizeSceneNameAnime, showNames)
    else:
        return map(sanitizeSceneName, showNames)


def makeSceneSeasonSearchString(show, ep_obj, extraSearchType=None):

    if show.air_by_date or show.sports:
        numseasons = 0

        # the search string for air by date shows is just
        seasonStrings = [str(ep_obj.airdate).split('-')[0]]
    elif show.is_anime:
        numseasons = 0
        seasonEps = show.getAllEpisodes(ep_obj.season)

        # get show qualities
        anyQualities, bestQualities = common.Quality.splitQuality(show.quality)

        # compile a list of all the episode numbers we need in this 'season'
        seasonStrings = []
        for episode in seasonEps:

            # get quality of the episode
            curCompositeStatus = episode.status
            curStatus, curQuality = common.Quality.splitCompositeStatus(curCompositeStatus)

            if bestQualities:
                highestBestQuality = max(bestQualities)
            else:
                highestBestQuality = 0

            # if we need a better one then add it to the list of episodes to fetch
            if (curStatus in (
                    common.DOWNLOADED,
                    common.SNATCHED) and curQuality < highestBestQuality) or curStatus == common.WANTED:
                ab_number = episode.scene_absolute_number
                if ab_number > 0:
                    seasonStrings.append("%02d" % ab_number)

    else:
        myDB = db.DBConnection()
        numseasonsSQlResult = myDB.select(
            "SELECT COUNT(DISTINCT season) as numseasons FROM tv_episodes WHERE showid = ? and season != 0",
            [show.indexerid])

        numseasons = int(numseasonsSQlResult[0][0])
        seasonStrings = ["S%02d" % int(ep_obj.scene_season)]

    showNames = set(makeSceneShowSearchStrings(show, ep_obj.scene_season))

    toReturn = []

    # search each show name
    for curShow in showNames:
        # most providers all work the same way
        if not extraSearchType:
            # if there's only one season then we can just use the show name straight up
            if numseasons == 1:
                toReturn.append(curShow)
            # for providers that don't allow multiple searches in one request we only search for Sxx style stuff
            else:
                for cur_season in seasonStrings:
                    if ep_obj.show.is_anime:
                        if ep_obj.show.release_groups is not None:
                            if len(show.release_groups.whitelist) > 0:
                                for keyword in show.release_groups.whitelist:
                                    toReturn.append(keyword + '.' + curShow+ "." + cur_season)
                    else:
                        toReturn.append(curShow + "." + cur_season)


    return toReturn


def makeSceneSearchString(show, ep_obj):
    myDB = db.DBConnection()
    numseasonsSQlResult = myDB.select(
        "SELECT COUNT(DISTINCT season) as numseasons FROM tv_episodes WHERE showid = ? and season != 0",
        [show.indexerid])
    numseasons = int(numseasonsSQlResult[0][0])

    # see if we should use dates instead of episodes
    if (show.air_by_date or show.sports) and ep_obj.airdate != datetime.date.fromordinal(1):
        epStrings = [str(ep_obj.airdate)]
    elif show.is_anime:
        epStrings = ["%02i" % int(ep_obj.scene_absolute_number if ep_obj.scene_absolute_number > 0 else ep_obj.scene_episode)]
    else:
        epStrings = ["S%02iE%02i" % (int(ep_obj.scene_season), int(ep_obj.scene_episode)),
                     "%ix%02i" % (int(ep_obj.scene_season), int(ep_obj.scene_episode))]

    # for single-season shows just search for the show name -- if total ep count (exclude s0) is less than 11
    # due to the amount of qualities and releases, it is easy to go over the 50 result limit on rss feeds otherwise
    if numseasons == 1 and not ep_obj.show.is_anime:
        epStrings = ['']

    showNames = set(makeSceneShowSearchStrings(show, ep_obj.scene_season))

    toReturn = []

    for curShow in showNames:
        for curEpString in epStrings:
            if ep_obj.show.is_anime:
                if ep_obj.show.release_groups is not None:
                    if len(ep_obj.show.release_groups.whitelist) > 0:
                        for keyword in ep_obj.show.release_groups.whitelist:
                            toReturn.append(keyword + '.' + curShow + '.' + curEpString)
                    elif len(ep_obj.show.release_groups.blacklist) == 0:
                        # If we have neither whitelist or blacklist we just append what we have
                        toReturn.append(curShow + '.' + curEpString)
            else:
                toReturn.append(curShow + '.' + curEpString)

    return toReturn


def isGoodResult(name, show, log=True, season=-1):
    """
    Use an automatically-created regex to make sure the result actually is the show it claims to be
    """

    all_show_names = allPossibleShowNames(show, season=season)
    showNames = map(sanitizeSceneName, all_show_names) + all_show_names
    showNames += map(ss, all_show_names)

    for curName in set(showNames):
        if not show.is_anime:
            escaped_name = re.sub('\\\\[\\s.-]', '\W+', re.escape(curName))
            if show.startyear:
                escaped_name += "(?:\W+" + str(show.startyear) + ")?"
            curRegex = '^' + escaped_name + '\W+(?:(?:S\d[\dE._ -])|(?:\d\d?x)|(?:\d{4}\W\d\d\W\d\d)|(?:(?:part|pt)[\._ -]?(\d|[ivx]))|Season\W+\d+\W+|E\d+\W+|(?:\d{1,3}.+\d{1,}[a-zA-Z]{2}\W+[a-zA-Z]{3,}\W+\d{4}.+))'
        else:
            escaped_name = re.sub('\\\\[\\s.-]', '[\W_]+', re.escape(curName))
            # FIXME: find a "automatically-created" regex for anime releases # test at http://regexr.com?2uon3
            curRegex = '^((\[.*?\])|(\d+[\.-]))*[ _\.]*' + escaped_name + '(([ ._-]+\d+)|([ ._-]+s\d{2})).*'

        if log:
            logger.log(u"Checking if show " + name + " matches " + curRegex, logger.DEBUG)

        match = re.search(curRegex, name, re.I)
        if match:
            logger.log(u"Matched " + curRegex + " to " + name, logger.DEBUG)
            return True

    if log:
        logger.log(
            u"Provider gave result " + name + " but that doesn't seem like a valid result for " + show.name + " so I'm ignoring it")
    return False


def allPossibleShowNames(show, season=-1):
    """
    Figures out every possible variation of the name for a particular show. Includes TVDB name, TVRage name,
    country codes on the end, eg. "Show Name (AU)", and any scene exception names.

    show: a TVShow object that we should get the names of

    Returns: a list of all the possible show names
    """

    showNames = get_scene_exceptions(show.indexerid, season=season)[:]
    if not showNames:  # if we dont have any season specific exceptions fallback to generic exceptions
        season = -1
        showNames = get_scene_exceptions(show.indexerid, season=season)[:]

    if season in [-1, 1]:
        showNames.append(show.name)

    if not show.is_anime:
        newShowNames = []
        country_list = common.countryList
        country_list.update(dict(zip(common.countryList.values(), common.countryList.keys())))
        for curName in set(showNames):
            if not curName:
                continue

            # if we have "Show Name Australia" or "Show Name (Australia)" this will add "Show Name (AU)" for
            # any countries defined in common.countryList
            # (and vice versa)
            for curCountry in country_list:
                if curName.endswith(' ' + curCountry):
                    newShowNames.append(curName.replace(' ' + curCountry, ' (' + country_list[curCountry] + ')'))
                elif curName.endswith(' (' + curCountry + ')'):
                    newShowNames.append(curName.replace(' (' + curCountry + ')', ' (' + country_list[curCountry] + ')'))

            # if we have "Show Name (2013)" this will strip the (2013) show year from the show name
            #newShowNames.append(re.sub('\(\d{4}\)','',curName))

        showNames += newShowNames

    return showNames

def determineReleaseName(dir_name=None, nzb_name=None):
    """Determine a release name from an nzb and/or folder name"""

    if nzb_name is not None:
        logger.log(u"Using nzb_name for release name.")
        return nzb_name.rpartition('.')[0]

    if dir_name is None:
        return None

    # try to get the release name from nzb/nfo
    file_types = ["*.nzb", "*.nfo"]

    for search in file_types:

        reg_expr = re.compile(fnmatch.translate(search), re.IGNORECASE)
        files = [file_name for file_name in ek(os.listdir, dir_name) if
                 ek(os.path.isfile, ek(os.path.join, dir_name, file_name))]
        results = filter(reg_expr.search, files)

        if len(results) == 1:
            found_file = ek(os.path.basename, results[0])
            found_file = found_file.rpartition('.')[0]
            if filterBadReleases(found_file):
                logger.log(u"Release name (" + found_file + ") found from file (" + results[0] + ")")
                return found_file.rpartition('.')[0]

    # If that fails, we try the folder
    folder = ek(os.path.basename, dir_name)
    if filterBadReleases(folder):
        # NOTE: Multiple failed downloads will change the folder name.
        # (e.g., appending #s)
        # Should we handle that?
        logger.log(u"Folder name (" + folder + ") appears to be a valid release name. Using it.", logger.DEBUG)
        return folder

    return None
