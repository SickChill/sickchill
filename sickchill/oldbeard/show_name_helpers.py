import fnmatch
import os
import re

import validators

from sickchill import logger, settings

from . import common
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from .scene_exceptions import get_scene_exceptions

resultFilters = {"sub(bed|ed|pack|s)", "(dir|sub|nfo)fix", "(?<!shomin.)sample", "(dvd)?extras", "dub(bed)?"}

if hasattr("General", "ignored_subs_list") and settings.IGNORED_SUBS_LIST:
    resultFilters.add("(" + settings.IGNORED_SUBS_LIST.replace(",", "|") + ")sub(bed|ed|s)?")


def containsAtLeastOneWord(name, words):
    """
    Filters out results based on filter_words

    name: name to check
    words : string of words separated by a ',' or list of words

    Returns: False if the name doesn't contain any word of words list, or the found word from the list.
    """
    if isinstance(words, str):
        words = words.split(",")

    words = {word.strip() for word in words if word.strip()}
    if not any(words):
        return True

    for word, regexp in {word: re.compile(r"(^|[\W_]){0}($|[\W_])".format(re.escape(word)), re.I) for word in words}.items():
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
        logger.debug("{0}".format(error))
        return False
    except InvalidShowException:
        pass
    # except InvalidShowException as error:
    #    logger.debug("{0}".format(error))
    #    return False

    def clean_set(words):
        return {x.strip() for x in set((words or "").lower().split(",")) if x.strip()}

    # if any of the bad strings are in the name then say no
    ignore_words = resultFilters
    ignore_words = ignore_words.union(clean_set(show and show.rls_ignore_words or ""))  # Show specific ignored words
    ignore_words = ignore_words.union(clean_set(settings.IGNORE_WORDS))  # Plus Global ignored words
    ignore_words = ignore_words.difference(clean_set(show and show.rls_require_words or ""))  # Minus show specific required words
    if settings.REQUIRE_WORDS and not (show and show.rls_ignore_words):  # Only remove global require words from the list if we arent using show ignore words
        ignore_words = ignore_words.difference(clean_set(settings.REQUIRE_WORDS))

    word = containsAtLeastOneWord(name, ignore_words)
    if word:
        logger.info("Release: {} contains {}, ignoring it".format(name, word))
        return False

    # if any of the good strings aren't in the name then say no
    require_words = set()
    require_words = require_words.union(clean_set(show and show.rls_require_words or ""))  # Show specific required words
    require_words = require_words.union(clean_set(settings.REQUIRE_WORDS))  # Plus Global required words
    require_words = require_words.difference(clean_set(show and show.rls_ignore_words or ""))  # Minus show specific ignored words
    if settings.IGNORE_WORDS and not (show and show.rls_require_words):  # Only remove global ignore words from the list if we arent using show require words
        require_words = require_words.difference(clean_set(settings.IGNORE_WORDS))

    if require_words and not containsAtLeastOneWord(name, require_words):
        logger.info("Release: " + name + " doesn't contain any of " + ", ".join(set(require_words)) + ", ignoring it")
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
        country_list.update({common.countryList[k]: k for k in common.countryList})
        for curName in set(showNames):
            if not curName:
                continue

            # if we have "Show Name Australia" or "Show Name (Australia)" this will add "Show Name (AU)" for
            # any countries defined in common.countryList
            # (and vice versa)
            for curCountry in country_list:
                if curName.endswith(" " + curCountry):
                    newShowNames.append(curName.replace(" " + curCountry, " (" + country_list[curCountry] + ")"))
                elif curName.endswith(" (" + curCountry + ")"):
                    newShowNames.append(curName.replace(" (" + curCountry + ")", " (" + country_list[curCountry] + ")"))

            # # if we have "Show Name (2013)" this will strip the (2013) show year from the show name
            # newShowNames.append(re.sub('\(\d{4}\)', '', curName))

        showNames += newShowNames

    return set(showNames)


def determine_release_name(directory=None, release_name=None):
    """Determine a release name from an nzb and/or folder name"""

    if release_name is not None:
        if validators.url(release_name) == True:
            logger.info(_("Downloader returned a download url rather than a release name"))
            return release_name

        logger.info(_("Using release for release name."))
        return release_name.rpartition(".")[0]

    if directory is None:
        return None

    # try to get the release name from nzb/nfo
    file_types = ["*.nzb", "*.nfo"]

    for search in file_types:

        reg_expr = re.compile(fnmatch.translate(search), re.I)
        files = [filename for filename in os.listdir(directory) if os.path.isfile(os.path.join(directory, filename))]

        results = [f for f in files if reg_expr.search(f)]

        if len(results) == 1:
            found_file = os.path.basename(results[0])
            found_file = found_file.rpartition(".")[0]
            if filter_bad_releases(found_file):
                logger.info("Release name (" + found_file + ") found from file (" + results[0] + ")")
                return found_file.rpartition(".")[0]

    # If that fails, we try the folder
    folder = os.path.basename(directory)
    if filter_bad_releases(folder):
        # NOTE: Multiple failed downloads will change the folder name.
        # (e.g., appending #s)
        # Should we handle that?
        logger.debug("Folder name (" + folder + ") appears to be a valid release name. Using it.")
        return folder

    return None


def hasPreferredWords(name, show=None):
    """Determine based on the full episode (file)name combined with the preferred words what the weight its preference should be"""

    name = name.lower()

    def clean_set(words):
        weighted_words = []

        words = words.lower().strip().split(",")
        val = len(words)

        for word in words:
            weighted_words.append({"word": word, "weight": val})
            val = val - 1

        return weighted_words

    prefer_words = []

    # Because we weigh values, we can not union global and show based values, so we don't do that
    if settings.PREFER_WORDS:
        prefer_words = clean_set(settings.PREFER_WORDS)
    if show and show.rls_prefer_words:
        prefer_words = clean_set(show.rls_prefer_words or "")

    # if nothing set, return position 0
    if len(prefer_words) <= 0:
        return 0

    value = 0
    for word_pair in prefer_words:
        if word_pair["weight"] > value and word_pair["word"] in name:
            value = word_pair["weight"]

    return value
