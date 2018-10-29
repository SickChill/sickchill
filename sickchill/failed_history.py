# coding=utf-8
# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
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

from __future__ import print_function, unicode_literals

import datetime
import re

from six.moves import urllib

from sickchill import db, logger
from sickchill.common import FAILED, Quality, WANTED
from sickchill.helper.encoding import ss
from sickchill.helper.exceptions import EpisodeNotFoundException, ex
from sickchill.show.History import History


def prepareFailedName(release):
    """Standardizes release name for failed DB"""

    fixed = urllib.parse.unquote(release)
    if fixed.endswith(".nzb"):
        fixed = fixed.rpartition(".")[0]

    fixed = re.sub(r"[\.\-\+\ ]", "_", fixed)
    fixed = ss(fixed)

    return fixed


def logFailed(release):
    log_str = ""
    size = -1
    provider = ""

    release = prepareFailedName(release)

    failed_db_con = db.DBConnection('failed.db')
    sql_results = failed_db_con.select("SELECT * FROM history WHERE release=?", [release])

    if not sql_results:
        logger.log(
            "Release not found in snatch history.", logger.WARNING)
    elif len(sql_results) > 1:
        logger.log("Multiple logged snatches found for release", logger.WARNING)
        sizes = len(set(x[b"size"] for x in sql_results))
        providers = len(set(x[b"provider"] for x in sql_results))
        if sizes == 1:
            logger.log("However, they're all the same size. Continuing with found size.", logger.WARNING)
            size = sql_results[0][b"size"]
        else:
            logger.log(
                "They also vary in size. Deleting the logged snatches and recording this release with no size/provider",
                logger.WARNING)
            for result in sql_results:
                deleteLoggedSnatch(result[b"release"], result[b"size"], result[b"provider"])

        if providers == 1:
            logger.log("They're also from the same provider. Using it as well.")
            provider = sql_results[0][b"provider"]
    else:
        size = sql_results[0][b"size"]
        provider = sql_results[0][b"provider"]

    if not hasFailed(release, size, provider):
        failed_db_con = db.DBConnection('failed.db')
        failed_db_con.action("INSERT INTO failed (release, size, provider) VALUES (?, ?, ?)", [release, size, provider])

    deleteLoggedSnatch(release, size, provider)

    return log_str


def logSuccess(release):
    release = prepareFailedName(release)

    failed_db_con = db.DBConnection('failed.db')
    failed_db_con.action("DELETE FROM history WHERE release=?", [release])


def hasFailed(release, size, provider="%"):
    """
    Returns True if a release has previously failed.

    If provider is given, return True only if the release is found
    with that specific provider. Otherwise, return True if the release
    is found with any provider.

    :param release: Release name to record failure
    :param size: Size of release
    :param provider: Specific provider to search (defaults to all providers)
    :return: True if a release has previously failed.
    """

    release = prepareFailedName(release)

    failed_db_con = db.DBConnection('failed.db')
    sql_results = failed_db_con.select(
        "SELECT release FROM failed WHERE release=? AND size=? AND provider LIKE ? LIMIT 1",
        [release, size, provider])

    return len(sql_results) > 0


def revertEpisode(epObj):
    """Restore the episodes of a failed download to their original state"""
    failed_db_con = db.DBConnection('failed.db')
    sql_results = failed_db_con.select("SELECT episode, old_status FROM history WHERE showid=? AND season=?",
                                       [epObj.show.indexerid, epObj.season])

    history_eps = {res[b"episode"]: res for res in sql_results}

    try:
        logger.log("Reverting episode ({0}, {1}): {2}".format(epObj.season, epObj.episode, epObj.name))
        with epObj.lock:
            if epObj.episode in history_eps:
                logger.log("Found in history")
                epObj.status = history_eps[epObj.episode][b'old_status']
            else:
                logger.log("Episode don't have a previous snatched status to revert. Setting it back to WANTED",
                           logger.DEBUG)
                epObj.status = WANTED
                epObj.saveToDB()

    except EpisodeNotFoundException as e:
        logger.log("Unable to create episode, please set its status manually: " + ex(e),
                   logger.WARNING)


def markFailed(epObj):
    """
    Mark an episode as failed

    :param epObj: Episode object to mark as failed
    :return: empty string
    """
    log_str = ""

    try:
        with epObj.lock:
            quality = Quality.splitCompositeStatus(epObj.status)[1]
            epObj.status = Quality.compositeStatus(FAILED, quality)
            epObj.saveToDB()

    except EpisodeNotFoundException as e:
        logger.log("Unable to get episode, please set its status manually: " + ex(e), logger.WARNING)

    return log_str


def logSnatch(searchResult):
    """
    Logs a successful snatch

    :param searchResult: Search result that was successful
    """
    logDate = datetime.datetime.today().strftime(History.date_format)
    release = prepareFailedName(searchResult.name)

    providerClass = searchResult.provider
    if providerClass is not None:
        provider = providerClass.name
    else:
        provider = "unknown"

    show_obj = searchResult.episodes[0].show

    failed_db_con = db.DBConnection('failed.db')
    for episode in searchResult.episodes:
        failed_db_con.action(
            "INSERT INTO history (date, size, release, provider, showid, season, episode, old_status)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [logDate, searchResult.size, release, provider, show_obj.indexerid, episode.season, episode.episode,
             episode.status])


def deleteLoggedSnatch(release, size, provider):
    """
    Remove a snatch from history

    :param release: release to delete
    :param size: Size of release
    :param provider: Provider to delete it from
    """
    release = prepareFailedName(release)

    failed_db_con = db.DBConnection('failed.db')
    failed_db_con.action("DELETE FROM history WHERE release=? AND size=? AND provider=?",
                         [release, size, provider])


def trimHistory():
    """Trims history table to 1 month of history from today"""
    failed_db_con = db.DBConnection('failed.db')
    failed_db_con.action("DELETE FROM history WHERE date < " + str(
        (datetime.datetime.today() - datetime.timedelta(days=30)).strftime(History.date_format)))


def findRelease(epObj):
    """
    Find releases in history by show ID and season.
    Return None for release if multiple found or no release found.
    """

    release = None
    provider = None

    # Clear old snatches for this release if any exist
    failed_db_con = db.DBConnection('failed.db')
    # failed_db_con.action(
    #     "DELETE FROM history WHERE showid = {0} AND season = {1} AND episode = {2}"
    #     " AND date < (SELECT max(date) FROM history WHERE showid = {0} AND season = {1} AND episode = {2})".format
    #     (epObj.show.indexerid, epObj.season, epObj.episode)
    # )

    # Search for release in snatch history
    results = failed_db_con.select("SELECT release, provider, date FROM history WHERE showid=? AND season=? AND episode=?",
                                   [epObj.show.indexerid, epObj.season, epObj.episode])

    for result in results:
        release = str(result[b"release"])
        provider = str(result[b"provider"])
        date = result[b"date"]

        # Clear any incomplete snatch records for this release if any exist
        failed_db_con.action("DELETE FROM history WHERE release=? AND date!=?", [release, date])

        # Found a previously failed release
        logger.log("Failed release found for season ({0}): ({1})".format(epObj.season, result[b"release"]), logger.DEBUG)
        return release, provider

    # Release was not found
    logger.log("No releases found for season ({0}) of ({1})".format(epObj.season, epObj.show.indexerid), logger.DEBUG)
    return release, provider
