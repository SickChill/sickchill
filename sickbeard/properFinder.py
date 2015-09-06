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
import traceback
import re

from search import pickBestResult

import sickbeard

from sickbeard import db
from sickbeard import exceptions
from sickbeard.exceptions import ex
from sickbeard import helpers, logger
from sickbeard import search

from sickbeard.common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, Quality, cpu_presets
from sickrage.show.History import History

from name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class ProperFinder():
    def __init__(self):
        self.amActive = False

    def run(self, force=False):
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
            run_at = u", next check in approx. " + (
                "%dh, %dm" % (hours, minutes) if 0 < hours else "%dm, %ds" % (minutes, seconds))

        logger.log(u"Completed the search for new propers%s" % run_at)

        self.amActive = False

    def _getProperList(self):
        propers = {}

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        # for each provider get a list of the
        origThreadName = threading.currentThread().name
        providers = [x for x in sickbeard.providers.sortedProviderList(sickbeard.RANDOMIZE_PROVIDERS) if x.isActive()]
        for curProvider in providers:
            threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"

            logger.log(u"Searching for any new PROPER releases from " + curProvider.name)

            try:
                curPropers = curProvider.findPropers(search_date)
            except exceptions.AuthException, e:
                logger.log(u"Authentication error: " + ex(e), logger.ERROR)
                continue
            except Exception, e:
                logger.log(u"Error while searching " + curProvider.name + ", skipping: " + ex(e), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for x in curPropers:
                if not re.search('(^|[\. _-])(proper|repack)([\. _-]|$)', x.name, re.I):
                    logger.log(u'findPropers returned a non-proper, we have caught and skipped it but please report this', logger.WARNING)
                    continue

                name = self._genericName(x.name)
                if not name in propers:
                    logger.log(u"Found new proper: " + x.name, logger.DEBUG)
                    x.provider = curProvider
                    propers[name] = x

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
            except InvalidShowException:
                logger.log(u"Unable to parse the filename " + curProper.name + " into a valid show", logger.DEBUG)
                continue

            if not parse_result.series_name:
                continue

            if not parse_result.episode_numbers:
                logger.log(
                    u"Ignoring " + curProper.name + " because it's for a full season rather than specific episode",
                    logger.DEBUG)
                continue

            logger.log(
                u"Successful match! Result " + parse_result.original_name + " matched to show " + parse_result.show.name,
                logger.DEBUG)

            # set the indexerid in the db to the show's indexerid
            curProper.indexerid = parse_result.show.indexerid

            # set the indexer in the db to the show's indexer
            curProper.indexer = parse_result.show.indexer

            # populate our Proper instance
            curProper.show = parse_result.show
            curProper.season = parse_result.season_number if parse_result.season_number is not None else 1
            curProper.episode = parse_result.episode_numbers[0]
            curProper.release_group = parse_result.release_group
            curProper.version = parse_result.version
            curProper.quality = Quality.nameQuality(curProper.name, parse_result.is_anime)
            curProper.content = None

            # filter release
            bestResult = pickBestResult(curProper, parse_result.show)
            if not bestResult:
                logger.log(u"Proper " + curProper.name + " were rejected by our release filters.", logger.DEBUG)
                continue

            # only get anime proper if it has release group and version
            if bestResult.show.is_anime:
                if not bestResult.release_group and bestResult.version == -1:
                    logger.log(u"Proper " + bestResult.name + " doesn't have a release group and version, ignoring it",
                               logger.DEBUG)
                    continue

            # check if we actually want this proper (if it's the right quality)
            myDB = db.DBConnection()
            sqlResults = myDB.select("SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                     [bestResult.indexerid, bestResult.season, bestResult.episode])
            if not sqlResults:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            oldStatus, oldQuality = Quality.splitCompositeStatus(int(sqlResults[0]["status"]))
            if oldStatus not in (DOWNLOADED, SNATCHED) or oldQuality != bestResult.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if bestResult.show.is_anime:
                myDB = db.DBConnection()
                sqlResults = myDB.select(
                    "SELECT release_group, version FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                    [bestResult.indexerid, bestResult.season, bestResult.episode])

                oldVersion = int(sqlResults[0]["version"])
                oldRelease_group = (sqlResults[0]["release_group"])

                if oldVersion > -1 and oldVersion < bestResult.version:
                    logger.log("Found new anime v" + str(bestResult.version) + " to replace existing v" + str(oldVersion))
                else:
                    continue

                if oldRelease_group != bestResult.release_group:
                    logger.log("Skipping proper from release group: " + bestResult.release_group + ", does not match existing release group: " + oldRelease_group)
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if bestResult.indexerid != -1 and (bestResult.indexerid, bestResult.season, bestResult.episode) not in map(
                    operator.attrgetter('indexerid', 'season', 'episode'), finalPropers):
                logger.log(u"Found a proper that we need: " + str(bestResult.name))
                finalPropers.append(bestResult)

        return finalPropers

    def _downloadPropers(self, properList):

        for curProper in properList:

            historyLimit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            myDB = db.DBConnection()
            historyResults = myDB.select(
                "SELECT resource FROM history " +
                "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? " +
                "AND action IN (" + ",".join([str(x) for x in Quality.SNATCHED + Quality.DOWNLOADED]) + ")",
                [curProper.indexerid, curProper.season, curProper.episode, curProper.quality,
                 historyLimit.strftime(History.date_format)])

            # if we didn't download this episode in the first place we don't know what quality to use for the proper so we can't do it
            if len(historyResults) == 0:
                logger.log(
                    u"Unable to find an original history entry for proper " + curProper.name + " so I'm not downloading it.")
                continue

            else:

                # make sure that none of the existing history downloads are the same proper we're trying to download
                clean_proper_name = self._genericName(helpers.remove_non_release_groups(curProper.name))
                isSame = False
                for curResult in historyResults:
                    # if the result exists in history already we need to skip it
                    if self._genericName(helpers.remove_non_release_groups(curResult["resource"])) == clean_proper_name:
                        isSame = True
                        break
                if isSame:
                    logger.log(u"This proper is already in history, skipping it", logger.DEBUG)
                    continue

                # get the episode object
                epObj = curProper.show.getEpisode(curProper.season, curProper.episode)

                # make the result object
                result = curProper.provider.getResult([epObj])
                result.show = curProper.show
                result.url = curProper.url
                result.name = curProper.name
                result.quality = curProper.quality
                result.release_group = curProper.release_group
                result.version = curProper.version
                result.content = curProper.content

                # snatch it
                search.snatchEpisode(result, SNATCHED_PROPER)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])

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
