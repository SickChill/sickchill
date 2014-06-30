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

import time
import datetime
import operator
import threading

import sickbeard

from sickbeard import db
from sickbeard import exceptions
from sickbeard.exceptions import ex
from sickbeard import helpers, logger, show_name_helpers
from sickbeard import providers
from sickbeard import search
from sickbeard import history

from sickbeard.common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, Quality

from name_parser.parser import NameParser, InvalidNameException


class ProperFinder():
    def __init__(self):
        self.amActive = False

    def __del__(self):
        pass

    def run(self, force=False):

        if not sickbeard.DOWNLOAD_PROPERS:
            return

        logger.log(u"Beginning the search for new propers")

        self.amActive = True

        propers = self._getProperList()

        if propers:
            self._downloadPropers(propers)

        self._set_lastProperSearch(datetime.datetime.today().toordinal())

        run_at = ""
        if None is sickbeard.properFinderScheduler.start_time:
            run_in = sickbeard.properFinderScheduler.lastRun + sickbeard.properFinderScheduler.cycleTime - datetime.datetime.now()
            hours, remainder = divmod(run_in.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            run_at = u", next check in approx. " + ("%dh, %dm" % (hours, minutes) if 0 < hours else "%dm, %ds" % (minutes, seconds))

        logger.log(u"Completed the search for new propers%s" % run_at)

        self.amActive = False

    def _getProperList(self):
        propers = {}

        # for each provider get a list of the
        origThreadName = threading.currentThread().name
        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]
        for curProvider in providers:
            threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"

            search_date = datetime.datetime.today() - datetime.timedelta(days=2)

            logger.log(u"Searching for any new PROPER releases from " + curProvider.name)
            try:
                curPropers = curProvider.findPropers(search_date)
            except exceptions.AuthException, e:
                logger.log(u"Authentication error: " + ex(e), logger.ERROR)
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for x in curPropers:
                name = self._genericName(x.name)
                if not name in propers:
                    logger.log(u"Found new proper: " + x.name, logger.DEBUG)
                    x.provider = curProvider
                    propers[name] = x

        # reset thread name back to original
        threading.currentThread().name = origThreadName

        # take the list of unique propers and get it sorted by
        sortedPropers = sorted(propers.values(), key=operator.attrgetter('date'), reverse=True)
        finalPropers = []
        for curProper in sortedPropers:

            try:
                myParser = NameParser(False)
                parse_result = myParser.parse(curProper.name)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + curProper.name + " into a valid episode", logger.DEBUG)
                continue

            if not parse_result.series_name:
                continue

            if not parse_result.show:
                continue

            if not parse_result.episode_numbers:
                logger.log(
                    u"Ignoring " + curProper.name + " because it's for a full season rather than specific episode",
                    logger.DEBUG)
                continue

            showObj = parse_result.show
            logger.log(
                u"Successful match! Result " + parse_result.original_name + " matched to show " + showObj.name,
                logger.DEBUG)

            # set the indexerid in the db to the show's indexerid
            curProper.indexerid = showObj.indexerid

            # set the indexer in the db to the show's indexer
            curProper.indexer = showObj.indexer

            # populate our Proper instance
            if parse_result.air_by_date or parse_result.sports:
                curProper.season = -1
                curProper.episode = parse_result.air_date or parse_result.sports_event_date
            else:
                if parse_result.is_anime:
                    logger.log(u"I am sorry '"+curProper.name+"' seams to be an anime proper seach is not yet suported", logger.DEBUG)
                    continue
                else:
                    curProper.season = parse_result.season_number if parse_result.season_number != None else 1
                    curProper.episode = parse_result.episode_numbers[0]

            curProper.quality = Quality.nameQuality(curProper.name, parse_result.is_anime)

            if not show_name_helpers.filterBadReleases(curProper.name):
                logger.log(u"Proper " + curProper.name + " isn't a valid scene release that we want, igoring it",
                           logger.DEBUG)
                continue

            if showObj.rls_ignore_words and search.filter_release_name(curProper.name, showObj.rls_ignore_words):
                logger.log(u"Ignoring " + curProper.name + " based on ignored words filter: " + showObj.rls_ignore_words,
                           logger.MESSAGE)
                continue

            if showObj.rls_require_words and not search.filter_release_name(curProper.name, showObj.rls_require_words):
                logger.log(u"Ignoring " + curProper.name + " based on required words filter: " + showObj.rls_require_words,
                           logger.MESSAGE)
                continue

            # if we have an air-by-date show then get the real season/episode numbers
            if (parse_result.air_by_date or parse_result.sports_event_date) and curProper.indexerid:
                logger.log(
                    u"Looks like this is an air-by-date or sports show, attempting to convert the date to season/episode",
                    logger.DEBUG)
                airdate = curProper.episode.toordinal()
                myDB = db.DBConnection()
                sql_result = myDB.select(
                    "SELECT season, episode FROM tv_episodes WHERE showid = ? and indexer = ? and airdate = ?",
                    [curProper.indexerid, curProper.indexer, airdate])

                if sql_result:
                    curProper.season = int(sql_result[0][0])
                    curProper.episodes = [int(sql_result[0][1])]
                else:
                    logger.log(u"Unable to find episode with date " + str(
                        curProper.episode) + " for show " + parse_result.series_name + ", skipping", logger.WARNING)
                    continue

            # check if we actually want this proper (if it's the right quality)
            myDB = db.DBConnection()
            sqlResults = myDB.select(
                "SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                [curProper.indexerid, curProper.season, curProper.episode])

            if not sqlResults:
                continue

            oldStatus, oldQuality = Quality.splitCompositeStatus(int(sqlResults[0]["status"]))

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            if oldStatus not in (DOWNLOADED, SNATCHED) or oldQuality != curProper.quality:
                continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if curProper.indexerid != -1 and (curProper.indexerid, curProper.season, curProper.episode) not in map(
                    operator.attrgetter('indexerid', 'season', 'episode'), finalPropers):
                logger.log(u"Found a proper that we need: " + str(curProper.name))
                finalPropers.append(curProper)

        return finalPropers

    def _downloadPropers(self, properList):

        for curProper in properList:

            historyLimit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            myDB = db.DBConnection()
            historyResults = myDB.select(
                "SELECT resource FROM history "
                "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? "
                "AND action IN (" + ",".join([str(x) for x in Quality.SNATCHED]) + ")",
                [curProper.indexerid, curProper.season, curProper.episode, curProper.quality,
                 historyLimit.strftime(history.dateFormat)])

            # if we didn't download this episode in the first place we don't know what quality to use for the proper so we can't do it
            if len(historyResults) == 0:
                logger.log(
                    u"Unable to find an original history entry for proper " + curProper.name + " so I'm not downloading it.")
                continue

            else:

                # make sure that none of the existing history downloads are the same proper we're trying to download
                isSame = False
                for curResult in historyResults:
                    # if the result exists in history already we need to skip it
                    if self._genericName(curResult["resource"]) == self._genericName(curProper.name):
                        isSame = True
                        break
                if isSame:
                    logger.log(u"This proper is already in history, skipping it", logger.DEBUG)
                    continue

                # get the episode object
                showObj = helpers.findCertainShow(sickbeard.showList, curProper.indexerid)
                if showObj == None:
                    logger.log(u"Unable to find the show with indexerid " + str(
                        curProper                                      .indexerid) + " so unable to download the proper", logger.ERROR)
                    continue
                epObj = showObj.getEpisode(curProper.season, curProper.episode)

                # make the result object
                result = curProper.provider.getResult([epObj])
                result.url = curProper.url
                result.name = curProper.name
                result.quality = curProper.quality

                # snatch it
                search.snatchEpisode(result, SNATCHED_PROPER)

    def _genericName(self, name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    def _set_lastProperSearch(self, when):

        logger.log(u"Setting the last Proper search in the DB to " + str(when), logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM info")

        if len(sqlResults) == 0:
            myDB.action("INSERT INTO info (last_backlog, last_indexer, last_proper_search) VALUES (?,?,?)",
                        [0, 0, str(when)])
        else:
            myDB.action("UPDATE info SET last_proper_search=" + str(when))

    def _get_lastProperSearch(self):

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM info")

        try:
            last_proper_search = datetime.date.fromordinal(int(sqlResults[0]["last_proper_search"]))
        except:
            return datetime.date.fromordinal(1)

        return last_proper_search
