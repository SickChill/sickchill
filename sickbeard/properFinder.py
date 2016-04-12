# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import re
import time
import datetime
import operator
import threading
import traceback
import sickbeard

from sickbeard import db
from sickbeard import helpers, logger
from sickbeard.search import snatchEpisode
from sickbeard.search import pickBestResult
from sickbeard.common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, Quality, cpu_presets
from sickrage.helper.exceptions import AuthException, ex
from sickrage.show.History import History
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class ProperFinder(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.am_active = False

    def run(self, force=False):  # pylint: disable=unused-argument
        """
        Start looking for new propers

        :param force: Start even if already running (currently not used, defaults to False)
        """
        logger.log(u"Beginning the search for new propers")

        self.am_active = True

        propers = self._getProperList()

        if propers:
            self._downloadPropers(propers)

        self._set_lastProperSearch(datetime.datetime.today().toordinal())

        run_at = ""
        if None is sickbeard.proper_search_scheduler.start_time:
            run_in = sickbeard.proper_search_scheduler.lastRun + sickbeard.proper_search_scheduler.cycle_time - datetime.datetime.now()
            hours, remainder = divmod(run_in.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            run_at = u", next check in approx. " + (
                "{0:d}h, {1:d}m".format(hours, minutes) if 0 < hours else "{0:d}m, {1:d}s".format(minutes, seconds))

        logger.log(u"Completed the search for new propers{0}".format(run_at))

        self.am_active = False

    def _getProperList(self):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """
        Walk providers for propers
        """
        propers = {}

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        # for each provider get a list of the
        original_thread_name = threading.current_thread().name
        providers = [x for x in sickbeard.providers.sorted_provider_list(sickbeard.RANDOMIZE_PROVIDERS) if x.is_active()]
        for cur_provider in providers:
            threading.current_thread().name = original_thread_name + " :: [" + cur_provider.name + "]"

            logger.log(u"Searching for any new PROPER releases from " + cur_provider.name)

            try:
                cur_propers = cur_provider.find_propers(search_date)
            except AuthException as e:
                logger.log(u"Authentication error: " + ex(e), logger.DEBUG)
                continue
            except Exception as e:
                logger.log(u"Exception while searching propers in " + cur_provider.name + ", skipping: " + ex(e), logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for x in cur_propers:
                if not re.search(r'(^|[\. _-])(proper|repack)([\. _-]|$)', x.name, re.I):
                    logger.log(u'find_propers returned a non-proper, we have caught and skipped it.', logger.DEBUG)
                    continue

                name = self._genericName(x.name)
                if name not in propers:
                    logger.log(u"Found new proper: " + x.name, logger.DEBUG)
                    x.provider = cur_provider
                    propers[name] = x

            threading.current_thread().name = original_thread_name

        # take the list of unique propers and get it sorted by
        sortedPropers = sorted(propers.values(), key=operator.attrgetter('date'), reverse=True)
        finalPropers = []

        for cur_proper in sortedPropers:

            try:
                parse_result = NameParser(False).parse(cur_proper.name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log(u"{0}".format(error), logger.DEBUG)
                continue

            if not parse_result.series_name:
                continue

            if not parse_result.episode_numbers:
                logger.log(
                    u"Ignoring " + cur_proper.name + " because it's for a full season rather than specific episode",
                    logger.DEBUG)
                continue

            logger.log(
                u"Successful match! Result " + parse_result.original_name + " matched to show " + parse_result.show.name,
                logger.DEBUG)

            # set the indexerid in the db to the show's indexerid
            cur_proper.indexerid = parse_result.show.indexerid

            # set the indexer in the db to the show's indexer
            cur_proper.indexer = parse_result.show.indexer

            # populate our Proper instance
            cur_proper.show = parse_result.show
            cur_proper.season = parse_result.season_number if parse_result.season_number is not None else 1
            cur_proper.episode = parse_result.episode_numbers[0]
            cur_proper.release_group = parse_result.release_group
            cur_proper.version = parse_result.version
            cur_proper.quality = Quality.nameQuality(cur_proper.name, parse_result.is_anime)
            cur_proper.content = None

            # filter release
            bestResult = pickBestResult(cur_proper, parse_result.show)
            if not bestResult:
                logger.log(u"Proper " + cur_proper.name + " were rejected by our release filters.", logger.DEBUG)
                continue

            # only get anime proper if it has release group and version
            if bestResult.show.is_anime:
                if not bestResult.release_group and bestResult.version == -1:
                    logger.log(u"Proper " + bestResult.name + " doesn't have a release group and version, ignoring it",
                               logger.DEBUG)
                    continue

            # check if we actually want this proper (if it's the right quality)
            main_db_con = db.DBConnection()
            sql_results = main_db_con.select("SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                             [bestResult.indexerid, bestResult.season, bestResult.episode])
            if not sql_results:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            old_status, old_quality = Quality.splitCompositeStatus(int(sql_results[0]["status"]))
            if old_status not in (DOWNLOADED, SNATCHED) or old_quality != bestResult.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if bestResult.show.is_anime:
                main_db_con = db.DBConnection()
                sql_results = main_db_con.select(
                    "SELECT release_group, version FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                    [bestResult.indexerid, bestResult.season, bestResult.episode])

                old_version = int(sql_results[0]["version"])
                old_release_group = (sql_results[0]["release_group"])

                if -1 < old_version < bestResult.version:
                    logger.log(u"Found new anime v" + str(bestResult.version) + " to replace existing v" + str(old_version))
                else:
                    continue

                if old_release_group != bestResult.release_group:
                    logger.log(u"Skipping proper from release group: " + bestResult.release_group + ", does not match existing release group: " + old_release_group)
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if bestResult.indexerid != -1 and (bestResult.indexerid, bestResult.season, bestResult.episode) not in {(p.indexerid, p.season, p.episode) for p in finalPropers}:
                logger.log(u"Found a proper that we need: " + str(bestResult.name))
                finalPropers.append(bestResult)

        return finalPropers

    def _downloadPropers(self, properList):
        """
        Download proper (snatch it)

        :param properList:
        """

        for cur_proper in properList:

            historyLimit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            main_db_con = db.DBConnection()
            historyResults = main_db_con.select(
                "SELECT resource FROM history " +
                "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? " +
                "AND action IN (" + ",".join([str(x) for x in Quality.SNATCHED + Quality.DOWNLOADED]) + ")",
                [cur_proper.indexerid, cur_proper.season, cur_proper.episode, cur_proper.quality,
                 historyLimit.strftime(History.date_format)])

            # if we didn't download this episode in the first place we don't know what quality to use for the proper so we can't do it
            if not historyResults:
                logger.log(
                    u"Unable to find an original history entry for proper " + cur_proper.name + " so I'm not downloading it.")
                continue

            else:

                # make sure that none of the existing history downloads are the same proper we're trying to download
                clean_proper_name = self._genericName(helpers.remove_non_release_groups(cur_proper.name))
                isSame = False
                for cur_result in historyResults:
                    # if the result exists in history already we need to skip it
                    if self._genericName(helpers.remove_non_release_groups(cur_result["resource"])) == clean_proper_name:
                        isSame = True
                        break
                if isSame:
                    logger.log(u"This proper is already in history, skipping it", logger.DEBUG)
                    continue

                # get the episode object
                epObj = cur_proper.show.get_episode(cur_proper.season, cur_proper.episode)

                # make the result object
                result = cur_proper.provider.get_result([epObj])
                result.show = cur_proper.show
                result.url = cur_proper.url
                result.name = cur_proper.name
                result.quality = cur_proper.quality
                result.release_group = cur_proper.release_group
                result.version = cur_proper.version
                result.content = cur_proper.content

                # snatch it
                snatchEpisode(result, SNATCHED_PROPER)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])

    @staticmethod
    def _genericName(name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    @staticmethod
    def _set_lastProperSearch(when):
        """
        Record last propersearch in DB

        :param when: When was the last proper search
        """

        logger.log(u"Setting the last Proper search in the DB to " + str(when), logger.DEBUG)

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_proper_search FROM info")

        if not sql_results:
            main_db_con.action("INSERT INTO info (last_backlog, last_indexer, last_proper_search) VALUES (?,?,?)",
                               [0, 0, str(when)])
        else:
            main_db_con.action("UPDATE info SET last_proper_search=" + str(when))

    @staticmethod
    def _get_lastProperSearch():
        """
        Find last propersearch from DB
        """

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_proper_search FROM info")

        try:
            last_proper_search = datetime.date.fromordinal(int(sql_results[0]["last_proper_search"]))
        except Exception:
            return datetime.date.fromordinal(1)

        return last_proper_search
