import datetime
import os

from sickchill import logger, settings, tv

from . import common
from .common import DOWNLOADED, Quality
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser

name_presets = ("%SN - %Sx%0E", "%SN - %Sx%0E - %EN", "%S.N.S%0SE%0E.%E.N", "%Sx%0E - %EN", "S%0SE%0E - %EN", "Season %0S/%S.N.S%0SE%0E.%Q.N-%RG")

name_anime_presets = name_presets

name_abd_presets = ("%SN - %A-D - %EN", "%S.N.%A.D.%E.N.%Q.N", "%Y/%0M/%S.N.%A.D.%E.N-%RG")

name_sports_presets = ("%SN - %A-D - %EN", "%S.N.%A.D.%E.N.%Q.N", "%Y/%0M/%S.N.%A.D.%E.N-%RG")


class TVShow(object):
    def __init__(self):
        self.name = "Show Name"
        self.genre = "Comedy"
        self.indexerid = 1
        self.air_by_date = 0
        self.sports = 0
        self.anime = 0
        self.scene = 0

    @property
    def is_anime(self):
        """
        Find out if show is anime
        :return: True if show is anime, False if not
        """
        return self.anime > 0

    @property
    def is_sports(self):
        """
        Find out if show is sports
        :return: True if show is sports, False if not
        """
        return self.sports > 0

    @property
    def is_scene(self):
        """
        Find out if show is scene numbering
        :return: True if show is scene numbering, False if not
        """
        return self.scene > 0


class TVEpisode(tv.TVEpisode):
    def __init__(self, season, episode, absolute_number, name):
        self.relatedEps = []
        self.name = name
        self.season = season
        self.episode = episode
        self.absolute_number = absolute_number
        self.scene_season = season
        self.scene_episode = episode
        self.scene_absolute_number = absolute_number
        self.airdate = datetime.date(2010, 3, 9)
        self.show = TVShow()
        self.status = Quality.compositeStatus(common.DOWNLOADED, common.Quality.SDTV)
        self.release_name = "Show.Name.S02E03.HDTV.XviD-SICKCHILL"
        self.is_proper = True


def check_force_season_folders(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name can still be parsed if you strip off the folders to determine if we need to force season folders
    to be enabled or not.

    :return: true if season folders need to be forced on or false otherwise.
    """
    if pattern is None:
        pattern = settings.NAMING_PATTERN

    valid = not validate_name(pattern, None, anime_type, file_only=True)

    if multi is not None:
        valid = valid or not validate_name(pattern, multi, anime_type, file_only=True)

    return valid


def check_valid_naming(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name is can be parsed back to its original form for both single and multi episodes.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = settings.NAMING_PATTERN

    logger.debug("Checking whether the pattern " + pattern + " is valid for a single episode")
    valid = validate_name(pattern, None, anime_type)

    if multi is not None:
        logger.debug("Checking whether the pattern " + pattern + " is valid for a multi episode")
        valid = valid and validate_name(pattern, multi, anime_type)

    return valid


def check_valid_abd_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an air-by-date format.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = settings.NAMING_PATTERN

    logger.debug("Checking whether the pattern " + pattern + " is valid for an air-by-date episode")
    valid = validate_name(pattern, abd=True)

    return valid


def check_valid_sports_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an sports format.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = settings.NAMING_PATTERN

    logger.debug("Checking whether the pattern " + pattern + " is valid for an sports episode")
    valid = validate_name(pattern, sports=True)

    return valid


def validate_name(pattern, multi=None, anime_type=None, file_only=False, abd=False, sports=False):
    """
    See if we understand a name

    :param pattern: Name to analyse
    :param multi: Is this a multi-episode name
    :param anime_type: Is this anime
    :param file_only: Is this just a file or a dir
    :param abd: Is air-by-date enabled
    :param sports: Is this sports
    :return: True if valid name, False if not
    """
    ep = generate_sample_ep(multi, abd, sports, anime_type)

    new_name = ep.formatted_filename(pattern, multi, anime_type) + ".ext"
    new_path = ep.formatted_dir(pattern, multi, anime_type)
    if not file_only:
        new_name = os.path.join(new_path, new_name)

    if not new_name:
        logger.debug("Unable to create a name out of " + pattern)
        return False

    logger.debug("Trying to parse " + new_name)

    try:
        result = NameParser(True, showObj=ep.show, naming_pattern=True).parse(new_name)
    except (InvalidNameException, InvalidShowException) as error:
        logger.debug("{0}".format(error))
        return False

    logger.debug("The name " + new_name + " parsed into " + str(result))

    if abd or sports:
        if result.air_date != ep.airdate:
            logger.debug("Air date incorrect in parsed episode, pattern isn't valid")
            return False
    elif anime_type != 3:
        if result.ab_episode_numbers and result.ab_episode_numbers != [x.absolute_number for x in [ep] + ep.relatedEps]:
            logger.debug("Absolute numbering incorrect in parsed episode, pattern isn't valid")
            return False
    else:
        if result.season_number != ep.season:
            logger.debug("Season number incorrect in parsed episode, pattern isn't valid")
            return False
        if result.episode_numbers != [x.episode for x in [ep] + ep.relatedEps]:
            logger.debug("Episode numbering incorrect in parsed episode, pattern isn't valid")
            return False

    return True


def generate_sample_ep(multi=None, abd=False, sports=False, anime_type=None):
    # make a fake episode object
    ep = TVEpisode(2, 3, 3, "Ep Name")

    ep._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
    ep._airdate = datetime.date(2011, 3, 9)

    if abd:
        ep._release_name = "Show.Name.2011.03.09.HDTV.XviD-SICKCHILL"
        ep.show.air_by_date = 1
    elif sports:
        ep._release_name = "Show.Name.2011.03.09.HDTV.XviD-SICKCHILL"
        ep.show.sports = 1
    else:
        if anime_type != 3:
            ep.show.anime = 1
            ep._release_name = "Show.Name.003.HDTV.XviD-SICKCHILL"
        else:
            ep._release_name = "Show.Name.S02E03.HDTV.XviD-SICKCHILL"

    if multi is not None:
        ep._name = "Ep Name (1)"

        if anime_type != 3:
            ep.show.anime = 1

            ep._release_name = "Show.Name.003-004.HDTV.XviD-SICKCHILL"

            secondEp = TVEpisode(2, 4, 4, "Ep Name (2)")
            secondEp._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            secondEp._release_name = ep._release_name

            ep.relatedEps.append(secondEp)
        else:
            ep._release_name = "Show.Name.S02E03E04E05.HDTV.XviD-SICKCHILL"

            secondEp = TVEpisode(2, 4, 4, "Ep Name (2)")
            secondEp._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            secondEp._release_name = ep._release_name

            thirdEp = TVEpisode(2, 5, 5, "Ep Name (3)")
            thirdEp._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            thirdEp._release_name = ep._release_name

            ep.relatedEps.append(secondEp)
            ep.relatedEps.append(thirdEp)

    return ep


def test_name(pattern, multi=None, abd=False, sports=False, anime_type=None):
    ep = generate_sample_ep(multi, abd, sports, anime_type)

    return {"name": ep.formatted_filename(pattern, multi, anime_type), "dir": ep.formatted_dir(pattern, multi, anime_type)}
