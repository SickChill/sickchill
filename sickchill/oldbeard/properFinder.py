import datetime
import operator
import re
import threading
import time
import traceback

from sickchill import logger, oldbeard, settings
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard.scdatetime import sctimeago
from sickchill.show.History import History

from . import db, helpers
from .common import cpu_presets, DOWNLOADED, Quality, SNATCHED, SNATCHED_PROPER
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from .search import pick_best_result, snatch_episode


class ProperFinder(object):
    def __init__(self):
        self.amActive = False

    # noinspection PyUnusedLocal
    def run(self, force=False):
        """
        Start looking for new propers

        :param force: Start even if already running (currently not used, defaults to False)
        """
        logger.info(_("Beginning the search for new propers"))

        self.amActive = True

        propers = self._get_propers()

        if propers:
            self._download_propers(propers)

        self._set_last_proper_search(datetime.datetime.today().toordinal())

        when = sctimeago(-settings.properFinderScheduler.timeLeft())
        logger.info(_("Completed the search for new propers, next check approximately {when}").format(when=when))

        self.amActive = False

    def _get_propers(self):
        """
        Walk providers for propers
        """
        propers = {}

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        # for each provider get a list of the proper releases
        original_thread_name = threading.current_thread().name
        providers = [x for x in oldbeard.providers.sorted_provider_list(settings.RANDOMIZE_PROVIDERS) if x.is_active]
        for provider in providers:
            threading.current_thread().name = f"{original_thread_name} :: [{provider.name}]"

            logger.info(_("Searching for any new PROPER releases from {name}").format(name=provider.name))

            try:
                provider_propers = provider.find_propers(search_date)
            except AuthException as error:
                logger.warning(_("Authentication error: {error}").format(error=error))
                continue
            except Exception as error:
                logger.exception(_("Exception while searching propers in {name}, skipping: {error}").format(name=provider.name, error=error))
                logger.debug(traceback.format_exc())
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for proper in provider_propers:
                if not re.search(r"\b(proper|repack|real)\b", proper.name, re.I):
                    logger.debug(_("find_propers returned a non-proper, we have caught and skipped it."))
                    continue

                name = self._generic_name(proper.name)
                if name not in propers:
                    logger.debug(_("Found new proper: {name}").format(name=proper.name))
                    proper.provider = provider
                    propers[name] = proper

            threading.current_thread().name = original_thread_name

        # take the list of unique propers and get it sorted by date
        sorted_propers = sorted(list(propers.values()), key=operator.attrgetter("date"), reverse=True)
        final_propers = []

        for proper in sorted_propers:
            try:
                parse_result = NameParser(False).parse(proper.name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.debug(_("Error parsing {name}: {error}").format(name=proper.name, error=error))
                continue

            if not parse_result.series_name:
                continue

            if parse_result.show.paused:
                logger.debug(_("Ignoring {name} because {show} is paused").format(name=proper.name, show=proper.show.name))
                continue

            if not parse_result.episode_numbers:
                logger.debug(_("Ignoring {name} because it's for a full season rather than specific episode").format(name=proper.name))
                continue

            logger.debug(
                _("Successful match! Result {name} matched to show {show_name}").format(name=parse_result.original_name, show_name=parse_result.show.name)
            )

            # set the indexerid in the db to the show's indexerid
            proper.indexerid = parse_result.show.indexerid

            # set the indexer in the db to the show's indexer
            proper.indexer = parse_result.show.indexer

            # populate our Proper instance
            proper.show = parse_result.show
            proper.season = parse_result.season_number if parse_result.season_number is not None else 1
            proper.episode = parse_result.episode_numbers[0]
            proper.release_group = parse_result.release_group
            proper.version = parse_result.version
            proper.quality = Quality.nameQuality(proper.name, parse_result.is_anime)
            proper.content = None

            # filter release
            best_result = pick_best_result(proper, parse_result.show)
            if not best_result:
                logger.debug(_("Proper {name} were rejected by our release filters").format(name=proper.name))
                continue

            # only get anime proper if it has release group and version
            if best_result.show.is_anime and not best_result.release_group and best_result.version == -1:
                logger.debug(_("Proper {name} doesn't have a release group and version, ignoring it").format(name=best_result.name))
                continue

            # check if we actually want this proper (if it's the right quality)
            main_db_con = db.DBConnection()
            sql_results = main_db_con.select(
                "SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                [best_result.indexerid, best_result.season, best_result.episode],
            )
            if not sql_results:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            old_status, old_quality = Quality.splitCompositeStatus(int(sql_results[0]["status"]))
            if old_status not in (DOWNLOADED, SNATCHED) or old_quality != best_result.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if best_result.show.is_anime:
                main_db_con = db.DBConnection()
                sql_results = main_db_con.select(
                    "SELECT release_group, version FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                    [best_result.indexerid, best_result.season, best_result.episode],
                )

                old_version = int(sql_results[0]["version"])
                old_release_group = sql_results[0]["release_group"]

                if -1 < old_version < best_result.version:
                    logger.info(_("Found new anime v{version} to replace existing v{old_version}").format(version=best_result.version, old_version=old_version))
                else:
                    continue

                if old_release_group != best_result.release_group:
                    logger.info(
                        "Skipping proper from release group: {release_group}, does not match existing release group: {old_release_group}".format(
                            release_group=best_result.release_group, old_release_group=old_release_group
                        )
                    )
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if best_result.indexerid != -1 and (best_result.indexerid, best_result.season, best_result.episode) not in {
                (p.indexerid, p.season, p.episode) for p in final_propers
            }:
                logger.info(_("Found a proper that we need: {name}").format(name=best_result.name))
                final_propers.append(best_result)

        return final_propers

    def _download_propers(self, proper_list):
        """
        Download proper (snatch it)

        :param proper_list:
        """

        for proper in proper_list:
            history_age = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            main_db_con = db.DBConnection()
            history_results = main_db_con.select(
                "SELECT resource FROM history "
                + "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? "
                + "AND action IN ("
                + ",".join([str(x) for x in Quality.SNATCHED + Quality.DOWNLOADED])
                + ")",
                [proper.indexerid, proper.season, proper.episode, proper.quality, history_age.strftime(History.date_format)],
            )

            # if we didn't download this episode in the first place we don't know what quality to use for the proper, so we can't do it
            if not history_results:
                logger.info(_("Unable to find an original history entry for proper {name} so I'm not downloading it.").format(name=proper.name))
                continue

            else:
                # make sure that none of the existing history downloads are the same proper we're trying to download
                clean_proper_name = self._generic_name(helpers.remove_non_release_groups(proper.name))
                is_same = False
                for result in history_results:
                    # if the result exists in history already we need to skip it
                    if self._generic_name(helpers.remove_non_release_groups(result["resource"])) == clean_proper_name:
                        is_same = True
                        break
                if is_same:
                    logger.debug(_("This proper is already in history, skipping it"))
                    continue

                # get the episode object
                episode_object = proper.show.getEpisode(proper.season, proper.episode)

                # make the result object
                result = proper.provider.get_result([episode_object])
                result.show = proper.show
                result.url = proper.url
                result.name = proper.name
                result.quality = proper.quality
                result.release_group = proper.release_group
                result.version = proper.version
                result.content = proper.content

                # snatch it
                snatch_episode(result, SNATCHED_PROPER)
                time.sleep(cpu_presets[settings.CPU_PRESET])

    @staticmethod
    def _generic_name(name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    @staticmethod
    def _set_last_proper_search(when):
        """
        Record last proper search in DB

        :param when: When was the last proper search
        """

        logger.debug(_("Setting the last Proper search in the DB to {when}").format(when=when))

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_proper_search FROM info")

        if not sql_results:
            main_db_con.action("INSERT INTO info (last_backlog, last_indexer, last_proper_search) VALUES (?,?,?)", [0, 0, str(when)])
        else:
            main_db_con.action(f"UPDATE info SET last_proper_search = ? WHERE 1", [str(when)])

    @staticmethod
    def _get_last_proper_search():
        """
        Find last proper search from DB
        """

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_proper_search FROM info")

        last_proper_search = datetime.date.min

        # noinspection PyBroadException
        try:
            last_proper_search = datetime.date.fromordinal(int(sql_results[0]["last_proper_search"]))
        except Exception:
            pass

        return last_proper_search
