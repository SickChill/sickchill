# Author: Tyler Fenby <tylerfenby@gmail.com>
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

import re
import urllib
import datetime

from sickbeard import db
from sickbeard import logger
from sickbeard.exceptions import ex, EpisodeNotFoundException
from sickbeard.common import Quality
from sickbeard.common import WANTED, FAILED
from sickbeard import encodingKludge as ek
from sickrage.show.History import History


def prepareFailedName(release):
    """Standardizes release name for failed DB"""

    fixed = urllib.unquote(release)
    if fixed.endswith(".nzb"):
        fixed = fixed.rpartition(".")[0]

    fixed = re.sub("[\.\-\+\ ]", "_", fixed)
    fixed = ek.ss(fixed)

    return fixed


def logFailed(release):
    log_str = u""
    size = -1
    provider = ""

    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select("SELECT * FROM history WHERE release=?", [release])

    if len(sql_results) == 0:
        logger.log(
            u"Release not found in snatch history.", logger.WARNING)
    elif len(sql_results) > 1:
        logger.log(u"Multiple logged snatches found for release", logger.WARNING)
        sizes = len(set(x["size"] for x in sql_results))
        providers = len(set(x["provider"] for x in sql_results))
        if sizes == 1:
            logger.log(u"However, they're all the same size. Continuing with found size.", logger.WARNING)
            size = sql_results[0]["size"]
        else:
            logger.log(
                u"They also vary in size. Deleting the logged snatches and recording this release with no size/provider",
                logger.WARNING)
            for result in sql_results:
                deleteLoggedSnatch(result["release"], result["size"], result["provider"])

        if providers == 1:
            logger.log(u"They're also from the same provider. Using it as well.")
            provider = sql_results[0]["provider"]
    else:
        size = sql_results[0]["size"]
        provider = sql_results[0]["provider"]

    if not hasFailed(release, size, provider):
        myDB = db.DBConnection('failed.db')
        myDB.action("INSERT INTO failed (release, size, provider) VALUES (?, ?, ?)", [release, size, provider])

    deleteLoggedSnatch(release, size, provider)

    return log_str


def logSuccess(release):
    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE release=?", [release])


def hasFailed(release, size, provider="%"):
    """
    Returns True if a release has previously failed.

    If provider is given, return True only if the release is found
    with that specific provider. Otherwise, return True if the release
    is found with any provider.
    """

    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select(
        "SELECT * FROM failed WHERE release=? AND size=? AND provider LIKE ?",
        [release, size, provider])

    return (len(sql_results) > 0)


def revertEpisode(epObj):
    """Restore the episodes of a failed download to their original state"""
    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select("SELECT * FROM history WHERE showid=? AND season=?",
                              [epObj.show.indexerid, epObj.season])

    history_eps = dict([(res["episode"], res) for res in sql_results])

    try:
        logger.log(u"Reverting episode (%s, %s): %s" % (epObj.season, epObj.episode, epObj.name))
        with epObj.lock:
            if epObj.episode in history_eps:
                logger.log(u"Found in history")
                epObj.status = history_eps[epObj.episode]['old_status']
            else:
                logger.log(u"WARNING: Episode not found in history. Setting it back to WANTED",
                           logger.WARNING)
                epObj.status = WANTED
                epObj.saveToDB()

    except EpisodeNotFoundException, e:
        logger.log(u"Unable to create episode, please set its status manually: " + ex(e),
                   logger.WARNING)


def markFailed(epObj):
    log_str = u""

    try:
        with epObj.lock:
            quality = Quality.splitCompositeStatus(epObj.status)[1]
            epObj.status = Quality.compositeStatus(FAILED, quality)
            epObj.saveToDB()

    except EpisodeNotFoundException, e:
        logger.log(u"Unable to get episode, please set its status manually: " + ex(e), logger.WARNING)

    return log_str


def logSnatch(searchResult):
    logDate = datetime.datetime.today().strftime(History.date_format)
    release = prepareFailedName(searchResult.name)

    providerClass = searchResult.provider
    if providerClass is not None:
        provider = providerClass.name
    else:
        provider = "unknown"

    show_obj = searchResult.episodes[0].show

    myDB = db.DBConnection('failed.db')
    for episode in searchResult.episodes:
        myDB.action(
            "INSERT INTO history (date, size, release, provider, showid, season, episode, old_status)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [logDate, searchResult.size, release, provider, show_obj.indexerid, episode.season, episode.episode,
             episode.status])


def deleteLoggedSnatch(release, size, provider):
    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE release=? AND size=? AND provider=?",
                [release, size, provider])


def trimHistory():
    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE date < " + str(
        (datetime.datetime.today() - datetime.timedelta(days=30)).strftime(History.date_format)))


def findRelease(epObj):
    """
    Find releases in history by show ID and season.
    Return None for release if multiple found or no release found.
    """

    release = None
    provider = None


    # Clear old snatches for this release if any exist
    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE showid=" + str(epObj.show.indexerid) + " AND season=" + str(
        epObj.season) + " AND episode=" + str(
        epObj.episode) + " AND date < (SELECT max(date) FROM history WHERE showid=" + str(
        epObj.show.indexerid) + " AND season=" + str(epObj.season) + " AND episode=" + str(epObj.episode) + ")")

    # Search for release in snatch history
    results = myDB.select("SELECT release, provider, date FROM history WHERE showid=? AND season=? AND episode=?",
                          [epObj.show.indexerid, epObj.season, epObj.episode])

    for result in results:
        release = str(result["release"])
        provider = str(result["provider"])
        date = result["date"]

        # Clear any incomplete snatch records for this release if any exist
        myDB.action("DELETE FROM history WHERE release=? AND date!=?", [release, date])

        # Found a previously failed release
        logger.log(u"Failed release found for season (%s): (%s)" % (epObj.season, result["release"]), logger.DEBUG)
        return (release, provider)

    # Release was not found
    logger.log(u"No releases found for season (%s) of (%s)" % (epObj.season, epObj.show.indexerid), logger.DEBUG)
    return (release, provider)