import datetime
import operator
import re
import threading
import time
import traceback

from sickchill import logger, oldbeard, settings
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import db, helpers
from sickchill.oldbeard.common import DOWNLOADED, SNATCHED, SNATCHED_PROPER, Quality, cpu_presets
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickchill.oldbeard.network_timezones import sc_now
from sickchill.oldbeard.scdatetime import sctimeago
from sickchill.oldbeard.search import pick_best_result, snatch_episode
from sickchill.show.History import History


class ProperFinder(object):
    def __init__(self):
        self.amActive = False

    # noinspection PyUnusedLocal
    def run(self, force=False):
        """
        Schedule a proper search on the SearchQueue (low priority) so it does not
        race daily/backlog provider traffic on the FINDPROPERS thread.

        :param force: Enqueue even if backlog is running
        """
        from sickchill.oldbeard.search_queue import ProperSearchQueueItem

        search_queue = settings.searchQueueScheduler.action
        if search_queue.is_proper_search_in_progress():
            logger.info(_("Proper search already queued or running, skipping"))
            return

        if not force and search_queue.is_backlog_in_progress():
            logger.info(_("Backlog in progress, deferring proper search until next cycle"))
            return

        search_queue.add_item(ProperSearchQueueItem(force=force))
        logger.info(_("Queued proper search on SEARCHQUEUE"))

    def run_search(self, force=False):
        """
        Perform the proper search (called from ProperSearchQueueItem).

        :param force: Currently unused; reserved for forced runs
        """
        if self.amActive:
            logger.debug(_("Proper search already active, skipping"))
            return

        logger.info(_("Beginning the search for new propers"))
        self.amActive = True
        try:
            propers = self._get_propers()

            if propers:
                self._download_propers(propers)

            self._set_last_proper_search(sc_now().toordinal())

            when = sctimeago(settings.properFinderScheduler.timeLeft())
            logger.info(_("Completed the search for new propers, next check approximately {when}").format(when=when))
        finally:
            self.amActive = False

    # Overlap when using last_proper_search so we do not miss edge releases
    _PROPER_OVERLAP = datetime.timedelta(hours=6)

    def _proper_search_date(self):
        """Incremental watermark: max(last_proper_search - overlap, now - max_window)."""
        now = sc_now()
        max_days = int(getattr(settings, "DOWNLOAD_PROPERS_WINDOW_DAYS", 2) or 2)
        max_days = min(7, max(1, max_days))
        floor = now - datetime.timedelta(days=max_days)
        last = self._get_last_proper_search()
        if last <= datetime.date.min:
            return floor
        last_dt = datetime.datetime.combine(last, datetime.time(), tzinfo=now.tzinfo)
        return max(last_dt - self._PROPER_OVERLAP, floor)

    def _get_propers(self):
        """
        Walk providers for propers
        """
        propers = {}

        search_date = self._proper_search_date()
        logger.debug(_("Proper search window starts at {when}").format(when=search_date))

        # for each provider get a list of the proper releases
        original_thread_name = threading.current_thread().name
        providers = [x for x in oldbeard.providers.sorted_provider_list(settings.RANDOMIZE_PROVIDERS) if x.is_active]
        for provider in providers:
            threading.current_thread().name = f"{original_thread_name} :: [{provider.name}]"

            logger.info(_("Searching for any new PROPER releases from {name}").format(name=provider.name))

            try:
                # Refresh RSS/cache under min_time so NZB/torrent list_propers sees recent titles
                # without forcing an extra hit when daily search already updated the cache.
                if getattr(provider, "cache", None) is not None:
                    try:
                        provider.cache.update_cache()
                    except Exception as error:
                        logger.debug(_("Cache update before propers failed for {name}: {error}").format(name=provider.name, error=error))

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
                if not re.search(r"\b(proper|repack|real)\b", proper.name, re.IGNORECASE):
                    logger.debug(_("find_propers returned a non-proper, we have caught and skipped it."))
                    continue

                name = self._generic_name(proper.name)
                if name not in propers:
                    logger.debug(_("Found new proper: {name}").format(name=proper.name))
                    proper.provider = provider
                    propers[name] = proper

            threading.current_thread().name = original_thread_name

        # take the list of unique propers and get it sorted by date
        sorted_propers = sorted(propers.values(), key=operator.attrgetter("date"), reverse=True)
        final_propers = []
        pack_seasons = set()

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

            is_season_pack = not parse_result.episode_numbers
            if is_season_pack and parse_result.season_number is None:
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
            proper.episode = parse_result.episode_numbers[0] if parse_result.episode_numbers else -1
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

            main_db_con = db.DBConnection()
            if is_season_pack:
                sql_results = main_db_con.select(
                    "SELECT episode, status FROM tv_episodes WHERE showid = ? AND season = ?",
                    [best_result.indexerid, best_result.season],
                )
                matching_status = 0
                for row in sql_results or []:
                    old_status, old_quality = Quality.splitCompositeStatus(int(row["status"]))
                    if old_status in (DOWNLOADED, SNATCHED) and old_quality == best_result.quality:
                        matching_status += 1
                if matching_status < 2:
                    continue
            else:
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
            if best_result.show.is_anime and not is_season_pack:
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

            history_age = sc_now() - datetime.timedelta(days=30)
            matched_history = self._fingerprint_matching_history(best_result, is_season_pack, history_age)
            if is_season_pack:
                if len(matched_history) < 2:
                    logger.debug(_("Ignoring season pack {name} because fewer than two history releases share its remainder").format(name=best_result.name))
                    continue
            elif not matched_history:
                logger.debug(_("Ignoring {name} because it does not match the original history release").format(name=best_result.name))
                continue

            if best_result.indexerid == -1:
                continue

            if is_season_pack:
                if (best_result.indexerid, best_result.season) in pack_seasons:
                    continue
                pack_seasons.add((best_result.indexerid, best_result.season))
                final_propers = [item for item in final_propers if not (item.indexerid == best_result.indexerid and item.season == best_result.season)]
                logger.info(_("Found a proper that we need: {name}").format(name=best_result.name))
                final_propers.append(best_result)
            elif (best_result.indexerid, best_result.season) not in pack_seasons and (best_result.indexerid, best_result.season, best_result.episode) not in {
                (item.indexerid, item.season, item.episode) for item in final_propers
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
            history_age = sc_now() - datetime.timedelta(days=30)
            is_season_pack = proper.episode < 1
            clean_proper_name = self._generic_name(helpers.remove_non_release_groups(proper.name))
            latest_resources = self._latest_history_resources(
                proper.indexerid,
                proper.season,
                None if is_season_pack else proper.episode,
                proper.quality,
                history_age,
            )

            if not latest_resources:
                logger.info(_("Unable to find an original history entry for proper {name} so I'm not downloading it.").format(name=proper.name))
                continue

            if any(self._generic_name(helpers.remove_non_release_groups(resource)) == clean_proper_name for resource in latest_resources.values()):
                logger.debug(_("This proper is already in history, skipping it"))
                continue

            episode_objects = []
            anime = bool(getattr(proper.show, "is_anime", False))
            for (season, episode), resource in latest_resources.items():
                if re.search(r"\b(proper|repack|real)\b", resource, re.IGNORECASE):
                    continue
                fingerprint = helpers.split_release_fingerprint(resource, anime=anime)
                if not helpers.release_matches_fingerprint(proper.name, fingerprint, require_episode=not is_season_pack, anime=anime):
                    continue
                episode_object = proper.show.get_episode(season, episode)
                if episode_object:
                    episode_objects.append(episode_object)

            if is_season_pack and len(episode_objects) < 2:
                logger.debug(_("Ignoring season pack {name} because fewer than two matching history episodes").format(name=proper.name))
                continue
            if not episode_objects:
                logger.debug(_("Ignoring {name} because it does not match the original history release").format(name=proper.name))
                continue

            result = proper.provider.get_result(episode_objects, proper.url)
            result.show = proper.show
            result.name = proper.name
            result.quality = proper.quality
            result.release_group = proper.release_group
            result.version = proper.version
            result.content = proper.content

            snatch_episode(result, SNATCHED_PROPER)
            time.sleep(cpu_presets[settings.CPU_PRESET])

    @staticmethod
    def _latest_history_resources(indexerid, season, episode, quality, since):
        """Latest snatch/download resource per episode in the history window."""
        main_db_con = db.DBConnection()
        actions = ",".join(str(action) for action in Quality.SNATCHED + Quality.DOWNLOADED)
        since_stamp = since.strftime(History.date_format)
        if episode is None or episode < 1:
            rows = main_db_con.select(
                "SELECT season, episode, resource FROM history "
                f"WHERE showid = ? AND season = ? AND quality = ? AND date >= ? AND action IN ({actions}) "
                "ORDER BY date DESC",
                [indexerid, season, quality, since_stamp],
            )
        else:
            rows = main_db_con.select(
                "SELECT season, episode, resource FROM history "
                f"WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? AND action IN ({actions}) "
                "ORDER BY date DESC",
                [indexerid, season, episode, quality, since_stamp],
            )
        latest = {}
        for row in rows or []:
            key = (int(row["season"]), int(row["episode"]))
            if key in latest:
                continue
            latest[key] = row["resource"] or ""
        return latest

    def _fingerprint_matching_history(self, proper, is_season_pack, since):
        latest = self._latest_history_resources(
            proper.indexerid,
            proper.season,
            None if is_season_pack else proper.episode,
            proper.quality,
            since,
        )
        anime = bool(getattr(proper.show, "is_anime", False))
        matched = {}
        for key, resource in latest.items():
            if re.search(r"\b(proper|repack|real)\b", resource, re.IGNORECASE):
                continue
            fingerprint = helpers.split_release_fingerprint(resource, anime=anime)
            if helpers.release_matches_fingerprint(proper.name, fingerprint, require_episode=not is_season_pack, anime=anime):
                matched[key] = resource
        return matched

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
            main_db_con.action("UPDATE info SET last_proper_search = ? WHERE 1", [str(when)])

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
