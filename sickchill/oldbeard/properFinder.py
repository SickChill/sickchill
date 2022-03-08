import datetime
import operator
import re
import threading
import time
import traceback

from sickchill import logger, oldbeard, settings
from sickchill.helper.exceptions import AuthException
from sickchill.show.History import History

from . import db, helpers
from .common import cpu_presets, DOWNLOADED, Quality, SNATCHED, SNATCHED_PROPER
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from .search import pickBestResult, snatchEpisode


class ProperFinder(object):
    def __init__(self):
        self.amActive = False

    def run(self, force=False):
        """
        Start looking for new propers

        :param force: Start even if already running (currently not used, defaults to False)
        """
        logger.info("Beginning the search for new propers")

        self.amActive = True

        propers = self._getProperList()

        if propers:
            self._downloadPropers(propers)

        self._set_lastProperSearch(datetime.datetime.today().toordinal())

        run_at = ""
        if settings.properFinderScheduler.start_time is None:
            run_in = settings.properFinderScheduler.lastRun + settings.properFinderScheduler.cycleTime - datetime.datetime.now()
            hours, remainder = divmod(run_in.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            run_at = ", next check in approx. " + ("{0:d}h, {1:d}m".format(hours, minutes) if hours > 0 else "{0:d}m, {1:d}s".format(minutes, seconds))

        logger.info("Completed the search for new propers{0}".format(run_at))

        self.amActive = False

    def _getProperList(self):
        """
        Walk providers for propers
        """
        propers = {}

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        # for each provider get a list of the
        original_thread_name = threading.current_thread().name
        providers = [x for x in oldbeard.providers.sortedProviderList(settings.RANDOMIZE_PROVIDERS) if x.is_active]
        for curProvider in providers:
            threading.current_thread().name = original_thread_name + " :: [" + curProvider.name + "]"

            logger.info("Searching for any new PROPER releases from " + curProvider.name)

            try:
                curPropers = curProvider.find_propers(search_date)
            except AuthException as e:
                logger.warning("Authentication error: " + str(e))
                continue
            except Exception as e:
                logger.exception("Exception while searching propers in " + curProvider.name + ", skipping: " + str(e))
                logger.debug(traceback.format_exc())
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for x in curPropers:
                if not re.search(r"\b(proper|repack|real)\b", x.name, re.I):
                    logger.debug("find_propers returned a non-proper, we have caught and skipped it.")
                    continue

                name = self._genericName(x.name)
                if name not in propers:
                    logger.debug("Found new proper: " + x.name)
                    x.provider = curProvider
                    propers[name] = x

            threading.current_thread().name = original_thread_name

        # take the list of unique propers and get it sorted by
        sortedPropers = sorted(list(propers.values()), key=operator.attrgetter("date"), reverse=True)
        finalPropers = []

        for curProper in sortedPropers:

            try:
                parse_result = NameParser(False).parse(curProper.name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.debug("{0}".format(error))
                continue

            if not parse_result.series_name:
                continue

            if parse_result.show.paused:
                logger.debug("Ignoring " + curProper.name + " because " + parse_result.show.name + " is paused")
                continue

            if not parse_result.episode_numbers:
                logger.debug("Ignoring " + curProper.name + " because it's for a full season rather than specific episode")
                continue

            logger.debug("Successful match! Result " + parse_result.original_name + " matched to show " + parse_result.show.name)

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
                logger.debug("Proper " + curProper.name + " were rejected by our release filters.")
                continue

            # only get anime proper if it has release group and version
            if bestResult.show.is_anime and not bestResult.release_group and bestResult.version == -1:
                logger.debug("Proper " + bestResult.name + " doesn't have a release group and version, ignoring it")
                continue

            # check if we actually want this proper (if it's the right quality)
            main_db_con = db.DBConnection()
            sql_results = main_db_con.select(
                "SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", [bestResult.indexerid, bestResult.season, bestResult.episode]
            )
            if not sql_results:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            oldStatus, oldQuality = Quality.splitCompositeStatus(int(sql_results[0]["status"]))
            if oldStatus not in (DOWNLOADED, SNATCHED) or oldQuality != bestResult.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if bestResult.show.is_anime:
                main_db_con = db.DBConnection()
                sql_results = main_db_con.select(
                    "SELECT release_group, version FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                    [bestResult.indexerid, bestResult.season, bestResult.episode],
                )

                oldVersion = int(sql_results[0]["version"])
                oldRelease_group = sql_results[0]["release_group"]

                if -1 < oldVersion < bestResult.version:
                    logger.info("Found new anime v" + str(bestResult.version) + " to replace existing v" + str(oldVersion))
                else:
                    continue

                if oldRelease_group != bestResult.release_group:
                    logger.info(
                        "Skipping proper from release group: " + bestResult.release_group + ", does not match existing release group: " + oldRelease_group
                    )
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if bestResult.indexerid != -1 and (bestResult.indexerid, bestResult.season, bestResult.episode) not in {
                (p.indexerid, p.season, p.episode) for p in finalPropers
            }:
                logger.info("Found a proper that we need: " + str(bestResult.name))
                finalPropers.append(bestResult)

        return finalPropers

    def _downloadPropers(self, properList):
        """
        Download proper (snatch it)

        :param properList:
        """

        for curProper in properList:
            historyLimit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            main_db_con = db.DBConnection()
            historyResults = main_db_con.select(
                "SELECT resource FROM history "
                + "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? "
                + "AND action IN ("
                + ",".join([str(x) for x in Quality.SNATCHED + Quality.DOWNLOADED])
                + ")",
                [curProper.indexerid, curProper.season, curProper.episode, curProper.quality, historyLimit.strftime(History.date_format)],
            )

            # if we didn't download this episode in the first place we don't know what quality to use for the proper so we can't do it
            if not historyResults:
                logger.info("Unable to find an original history entry for proper " + curProper.name + " so I'm not downloading it.")
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
                    logger.debug("This proper is already in history, skipping it")
                    continue

                # get the episode object
                epObj = curProper.show.getEpisode(curProper.season, curProper.episode)

                # make the result object
                result = curProper.provider.get_result([epObj])
                result.show = curProper.show
                result.url = curProper.url
                result.name = curProper.name
                result.quality = curProper.quality
                result.release_group = curProper.release_group
                result.version = curProper.version
                result.content = curProper.content

                # snatch it
                snatchEpisode(result, SNATCHED_PROPER)
                time.sleep(cpu_presets[settings.CPU_PRESET])

    @staticmethod
    def _genericName(name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    @staticmethod
    def _set_lastProperSearch(when):
        """
        Record last propersearch in DB

        :param when: When was the last proper search
        """

        logger.debug("Setting the last Proper search in the DB to " + str(when))

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_proper_search FROM info")

        if not sql_results:
            main_db_con.action("INSERT INTO info (last_backlog, last_indexer, last_proper_search) VALUES (?,?,?)", [0, 0, str(when)])
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
            return datetime.date.min

        return last_proper_search
