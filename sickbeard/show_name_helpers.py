# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import fnmatch
import os
import re

# Third Party Imports
import six

# First Party Imports
import sickbeard
from sickbeard import common, logger
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickbeard.scene_exceptions import get_scene_exceptions
from sickchill.helper.encoding import ek

resultFilters = {
    "sub(bed|ed|pack|s)",
    "(dir|sub|nfo)fix",
    "(?<!shomin.)sample",
    "(dvd)?extras",
    "dub(bed)?"
}

if hasattr('General', 'ignored_subs_list') and sickbeard.IGNORED_SUBS_LIST:
    resultFilters.add("(" + sickbeard.IGNORED_SUBS_LIST.replace(",", "|") + ")sub(bed|ed|s)?")


def containsAtLeastOneWord(name, words):
    """
    Filters out results based on filter_words

    name: name to check
    words : string of words separated by a ',' or list of words

    Returns: False if the name doesn't contain any word of words list, or the found word from the list.
    """
    if isinstance(words, six.string_types):
        words = words.split(',')

    words = {word.strip() for word in words if word.strip()}
    if not any(words):
        return True

    for word, regexp in six.iteritems(
        {word: re.compile(r'(^|[\W_]){0}($|[\W_])'.format(re.escape(word)), re.I) for word in words}
    ):
        if regexp.search(name):
            return word
    return False


def filter_bad_releases(name, parse=True, show=None):
    """
    Filters out non-english and just all-around stupid releases by comparing them
    to the resultFilters contents.

    name: the release name to check

    Returns: True if the release name is OK, False if it's bad.
    """

    try:
        if parse:
            NameParser().parse(name)
    except InvalidNameException as error:
        logger.log("{0}".format(error), logger.DEBUG)
        return False
    except InvalidShowException:
        pass
    # except InvalidShowException as error:
    #    logger.log(u"{0}".format(error), logger.DEBUG)
    #    return False

    def clean_set(words):
        return {x.strip() for x in set((words or '').lower().split(',')) if x.strip()}

    # if any of the bad strings are in the name then say no
    ignore_words = resultFilters
    ignore_words = ignore_words.union(clean_set(show and show.rls_ignore_words or ''))  # Show specific ignored words
    ignore_words = ignore_words.union(clean_set(sickbeard.IGNORE_WORDS))  # Plus Global ignored words
    ignore_words = ignore_words.difference(clean_set(show and show.rls_require_words or ''))  # Minus show specific required words
    if sickbeard.REQUIRE_WORDS and not (show and show.rls_ignore_words):  # Only remove global require words from the list if we arent using show ignore words
        ignore_words = ignore_words.difference(clean_set(sickbeard.REQUIRE_WORDS))

    word = containsAtLeastOneWord(name, ignore_words)
    if word:
        logger.log("Release: " + name + " contains " + word + ", ignoring it", logger.INFO)
        return False

    # if any of the good strings aren't in the name then say no
    require_words = set()
    require_words = require_words.union(clean_set(show and show.rls_require_words or ''))  # Show specific required words
    require_words = require_words.union(clean_set(sickbeard.REQUIRE_WORDS))  # Plus Global required words
    require_words = require_words.difference(clean_set(show and show.rls_ignore_words or ''))  # Minus show specific ignored words
    if sickbeard.IGNORE_WORDS and not (show and show.rls_require_words):  # Only remove global ignore words from the list if we arent using show require words
        require_words = require_words.difference(clean_set(sickbeard.IGNORE_WORDS))

    if require_words and not containsAtLeastOneWord(name, require_words):
        logger.log("Release: " + name + " doesn't contain any of " + ', '.join(set(require_words)) +
                   ", ignoring it", logger.INFO)
        return False

    return True


def allPossibleShowNames(show, season=-1):
    """
    Figures out every possible variation of the name for a particular show. Includes TVDB name, TVRage name,
    country codes on the end, eg. "Show Name (AU)", and any scene exception names.

    show: a TVShow object that we should get the names of

    Returns: a list of all the possible show names
    """

    showNames = get_scene_exceptions(show.indexerid, season=season)
    if not showNames:  # if we dont have any season specific exceptions fallback to generic exceptions
        season = -1
        showNames = get_scene_exceptions(show.indexerid, season=season)

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

            # # if we have "Show Name (2013)" this will strip the (2013) show year from the show name
            # newShowNames.append(re.sub('\(\d{4}\)', '', curName))

        showNames += newShowNames

    return set(showNames)


def determineReleaseName(dir_name=None, nzb_name=None):
    """Determine a release name from an nzb and/or folder name"""

    if nzb_name is not None:
        logger.log("Using nzb_name for release name.")
        return nzb_name.rpartition('.')[0]

    if dir_name is None:
        return None

    # try to get the release name from nzb/nfo
    file_types = ["*.nzb", "*.nfo"]

    for search in file_types:

        reg_expr = re.compile(fnmatch.translate(search), re.I)
        files = [file_name for file_name in ek(os.listdir, dir_name) if
                 ek(os.path.isfile, ek(os.path.join, dir_name, file_name))]

        results = [f for f in files if reg_expr.search(f)]

        if len(results) == 1:
            found_file = ek(os.path.basename, results[0])
            found_file = found_file.rpartition('.')[0]
            if filter_bad_releases(found_file):
                logger.log("Release name (" + found_file + ") found from file (" + results[0] + ")")
                return found_file.rpartition('.')[0]

    # If that fails, we try the folder
    folder = ek(os.path.basename, dir_name)
    if filter_bad_releases(folder):
        # NOTE: Multiple failed downloads will change the folder name.
        # (e.g., appending #s)
        # Should we handle that?
        logger.log("Folder name (" + folder + ") appears to be a valid release name. Using it.", logger.DEBUG)
        return folder

    return None


def hasPreferredWords(name, show=None):
    """Determine based on the full episode (file)name combined with the preferred words what the weight its preference should be"""

    name = name.lower()

    def clean_set(words):
        weighted_words = []

        words = words.lower().strip().split(',')
        val = len(words)

        for word in words:
            weighted_words.append({"word": word, "weight": val})
            val = val - 1

        return weighted_words

    prefer_words = []

    ## Because we weigh values, we can not union global and show based values, so we don't do that
    if sickbeard.PREFER_WORDS:
        prefer_words = clean_set(sickbeard.PREFER_WORDS)
    if show and show.rls_prefer_words:
        prefer_words = clean_set(show.rls_prefer_words or '')

    ## if nothing set, return position 0
    if len(prefer_words) <= 0:
        return 0

    value = 0
    for word_pair in prefer_words:
        if word_pair['weight'] > value and word_pair['word'] in name:
            value = word_pair['weight']

    return value
