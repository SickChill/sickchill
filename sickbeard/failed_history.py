# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import re
import urllib
import datetime

from sickbeard import db
from sickbeard import logger
from sickbeard import exceptions
from sickbeard.history import dateFormat
from sickbeard.common import Quality
from sickbeard.common import WANTED, FAILED


def _log_helper(message, level=logger.MESSAGE):
    logger.log(message, level)
    return message + u"\n"


def prepareFailedName(release):
    """Standardizes release name for failed DB"""

    fixed = urllib.unquote(release)
    if (fixed.endswith(".nzb")):
        fixed = fixed.rpartition(".")[0]

    fixed = re.sub("[\.\-\+\ ]", "_", fixed)
    return fixed


def logFailed(release):
    log_str = u""
    size = -1
    provider = ""

    release = prepareFailedName(release)

    myDB = db.DBConnection("failed.db")
    sql_results = myDB.select("SELECT * FROM history WHERE release=?", [release])

    if len(sql_results) == 0:
        log_str += _log_helper(
            u"Release not found in snatch history. Recording it as bad with no size and no proivder.", logger.WARNING)
        log_str += _log_helper(
            u"Future releases of the same name from providers that don't return size will be skipped.", logger.WARNING)
    elif len(sql_results) > 1:
        log_str += _log_helper(u"Multiple logged snatches found for release", logger.WARNING)
        sizes = len(set(x["size"] for x in sql_results))
        providers = len(set(x["provider"] for x in sql_results))
        if sizes == 1:
            log_str += _log_helper(u"However, they're all the same size. Continuing with found size.", logger.WARNING)
            size = sql_results[0]["size"]
        else:
            log_str += _log_helper(
                u"They also vary in size. Deleting the logged snatches and recording this release with no size/provider",
                logger.WARNING)
            for result in sql_results:
                deleteLoggedSnatch(result["release"], result["size"], result["provider"])

        if providers == 1:
            log_str += _log_helper(u"They're also from the same provider. Using it as well.")
            provider = sql_results[0]["provider"]
    else:
        size = sql_results[0]["size"]
        provider = sql_results[0]["provider"]

    if not hasFailed(release, size, provider):
        myDB.action("INSERT INTO failed (release, size, provider) VALUES (?, ?, ?)", [release, size, provider])

    deleteLoggedSnatch(release, size, provider)

    return log_str


def logSuccess(release):
    myDB = db.DBConnection("failed.db")

    release = prepareFailedName(release)

    myDB.action("DELETE FROM history WHERE release=?", [release])


def hasFailed(release, size, provider="%"):
    """
    Returns True if a release has previously failed.

    If provider is given, return True only if the release is found
    with that specific provider. Otherwise, return True if the release
    is found with any provider.
    """

    myDB = db.DBConnection("failed.db")
    sql_results = myDB.select(
        "SELECT * FROM failed WHERE release=? AND size=? AND provider LIKE ?",
        [prepareFailedName(release), size, provider])

    return (len(sql_results) > 0)


def revertEpisode(show_obj, season, episode=None):
    """Restore the episodes of a failed download to their original state"""
    myDB = db.DBConnection("failed.db")
    log_str = u""

    sql_results = myDB.select("SELECT * FROM history WHERE showid=? AND season=?", [show_obj.indexerid, season])
    # {episode: result, ...}
    history_eps = dict([(res["episode"], res) for res in sql_results])

    if episode:
        try:
            ep_obj = show_obj.getEpisode(season, episode)
            log_str += _log_helper(u"Reverting episode (%s, %s): %s" % (season, episode, ep_obj.name))
            with ep_obj.lock:
                if episode in history_eps:
                    log_str += _log_helper(u"Found in history")
                    ep_obj.status = history_eps[episode]['old_status']
                else:
                    log_str += _log_helper(u"WARNING: Episode not found in history. Setting it back to WANTED",
                                           logger.WARNING)
                    ep_obj.status = WANTED

                ep_obj.saveToDB()

        except exceptions.EpisodeNotFoundException, e:
            log_str += _log_helper(u"Unable to create episode, please set its status manually: " + exceptions.ex(e),
                                   logger.WARNING)
    else:
        # Whole season
        log_str += _log_helper(u"Setting season to wanted: " + str(season))
        for ep_obj in show_obj.getAllEpisodes(season):
            log_str += _log_helper(u"Reverting episode (%d, %d): %s" % (season, ep_obj.episode, ep_obj.name))
            with ep_obj.lock:
                if ep_obj in history_eps:
                    log_str += _log_helper(u"Found in history")
                    ep_obj.status = history_eps[ep_obj]['old_status']
                else:
                    log_str += _log_helper(u"WARNING: Episode not found in history. Setting it back to WANTED",
                                           logger.WARNING)
                    ep_obj.status = WANTED

                ep_obj.saveToDB()

    return log_str


def markFailed(show_obj, season, episode=None):
    log_str = u""

    if episode:
        try:
            ep_obj = show_obj.getEpisode(season, episode)

            with ep_obj.lock:
                quality = Quality.splitCompositeStatus(ep_obj.status)[1]
                ep_obj.status = Quality.compositeStatus(FAILED, quality)
                ep_obj.saveToDB()

        except exceptions.EpisodeNotFoundException, e:
            log_str += _log_helper(u"Unable to get episode, please set its status manually: " + exceptions.ex(e),
                                   logger.WARNING)
    else:
        # Whole season
        for ep_obj in show_obj.getAllEpisodes(season):
            with ep_obj.lock:
                quality = Quality.splitCompositeStatus(ep_obj.status)[1]
                ep_obj.status = Quality.compositeStatus(FAILED, quality)
                ep_obj.saveToDB()

    return log_str


def logSnatch(searchResult):
    myDB = db.DBConnection("failed.db")

    logDate = datetime.datetime.today().strftime(dateFormat)
    release = prepareFailedName(searchResult.name)

    providerClass = searchResult.provider
    if providerClass is not None:
        provider = providerClass.name
    else:
        provider = "unknown"

    show_obj = searchResult.episodes[0].show

    for episode in searchResult.episodes:
        old_status = show_obj.getEpisode(episode.season, episode.episode).status

        myDB.action(
            "INSERT INTO history (date, size, release, provider, showid, season, episode, old_status)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [logDate, searchResult.size, release, provider, show_obj.indexerid, episode.season, episode.episode,
             old_status])


def deleteLoggedSnatch(release, size, provider):
    myDB = db.DBConnection("failed.db")

    release = prepareFailedName(release)

    myDB.action("DELETE FROM history WHERE release=? AND size=? AND provider=?",
                [release, size, provider])


def trimHistory():
    myDB = db.DBConnection("failed.db")
    myDB.action("DELETE FROM history WHERE date < " + str(
        (datetime.datetime.today() - datetime.timedelta(days=30)).strftime(dateFormat)))


def findRelease(show, season, episode):
    """
    Find releases in history by show ID and season.
    Return None for release if multiple found or no release found.
    """
    if not show: return (None, None, None)
    if not season: return (None, None, None)

    release = None
    provider = None

    myDB = db.DBConnection("failed.db")

    # Clear old snatches for this release if any exist
    myDB.action("DELETE FROM history WHERE showid=" + str(show.indexerid) + " AND season=" + str(
        season) + " AND episode=" + str(episode) + " AND date < (SELECT max(date) FROM history WHERE showid=" + str(
        show.indexerid) + " AND season=" + str(season) + " AND episode=" + str(episode) + ")")

    # Search for release in snatch history
    results = myDB.select("SELECT release, provider, date FROM history WHERE showid=? AND season=? AND episode=?",
                          [show.indexerid, season, episode])

    for result in results:
        release = str(result["release"])
        provider = str(result["provider"])
        date = result["date"]

        # Clear any incomplete snatch records for this release if any exist
        myDB.action("DELETE FROM history WHERE release=? AND date!=?", [release, date])

        # Found a previously failed release
        logger.log(u"Failed release found for season (%s): (%s)" % (season, result["release"]), logger.DEBUG)
        return (release, provider)

    # Release was not found
    logger.log(u"No releases found for season (%s) of (%s)" % (season, show.indexerid), logger.DEBUG)
    return (release, provider)