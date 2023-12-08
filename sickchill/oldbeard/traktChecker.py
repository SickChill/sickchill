import datetime
import os
import traceback

import sickchill
from sickchill import logger, settings
from sickchill.helper.common import episode_num, sanitize_filename
from sickchill.oldbeard.trakt_api import TraktAPI, traktException
from sickchill.show.Show import Show

from . import db, helpers, search_queue
from .common import Quality, SKIPPED, UNKNOWN, WANTED


class TraktChecker(object):
    def __init__(self):
        self.trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)
        self.wanted_episode_queue = []
        self.show_watchlist = {}
        self.episode_watchlist = {}
        self.collection_list = {}
        self.amActive = False

    def run(self, force=False):
        self.amActive = True

        # add shows from trakt.tv watchlist
        if settings.TRAKT_SYNC_WATCHLIST:
            self.wanted_episode_queue = []  # its about to all get re-added
            if len(settings.ROOT_DIRS.split("|")) < 2:
                logger.warning("No default root directory")
                return

            try:
                self._sync_watchlists()
            except Exception:
                logger.debug(traceback.format_exc())

            try:
                # sync trakt.tv library with sickchill library
                self._sync_sickchill_to_trakt()
            except Exception:
                logger.debug(traceback.format_exc())

        self.amActive = False

    def _trakt_knows_show(self, indexer, indexerid):
        trakt_show = None

        try:
            library = self.trakt_api.traktRequest("sync/collection/shows") or []
            if not library:
                logger.debug("No shows found in your library, aborting library update")
                return

            trakt_show = [x for x in library if int(indexerid) == int(x["show"]["ids"][sickchill.indexer.slug(indexer)] or -1)]
        except traktException as error:
            logger.warning(f"Could not connect to Trakt service. Aborting library check. Error: {error}")

        return trakt_show

    def remove_show_from_trakt_library(self, show_obj):
        if self._trakt_knows_show(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data = {"shows": [{"title": show_obj.name, "year": show_obj.startyear, "ids": {show_obj.idxr.slug: show_obj.indexerid}}]}

            logger.debug("Removing {0} from trakt.tv library".format(show_obj.name))

            try:
                self.trakt_api.traktRequest("sync/collection/remove", data, method="POST")
            except traktException as error:
                logger.warning(f"Could not connect to Trakt service. Aborting removing show {show_obj.name} from Trakt library. Error: {error}")

    def add_show_to_trakt_library(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """
        if not self._trakt_knows_show(show_obj.indexer, show_obj.indexerid):
            # URL parameters
            data = {"shows": [{"title": show_obj.name, "year": show_obj.startyear, "ids": {show_obj.idxr.slug: show_obj.indexerid}}]}

            logger.debug("Adding {0} to trakt.tv library".format(show_obj.name))

            try:
                self.trakt_api.traktRequest("sync/collection", data, method="POST")
            except traktException as error:
                logger.warning(f"Could not connect to Trakt service. Aborting adding show {show_obj.name} to Trakt library. Error: {error}")
                return

    def _sync_sickchill_to_trakt(self):
        if settings.TRAKT_SYNC and settings.USE_TRAKT:
            logger.debug("Sync SickChill with Trakt Collection")

            if self._get_shows_collection():
                self._add_episodes_to_trakt_collection()
                if settings.TRAKT_SYNC_REMOVE:
                    self._remove_episode_from_trakt_collection()

    def _remove_episode_from_trakt_collection(self):
        if settings.TRAKT_SYNC_REMOVE and settings.TRAKT_SYNC and settings.USE_TRAKT:
            logger.debug("COLLECTION::REMOVE::START - Look for Episodes to Remove From Trakt Collection")

            main_db_con = db.DBConnection()
            sql_selection = "select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status, tv_episodes.location from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid"
            trakt_data = []

            for cur_episode in main_db_con.select(sql_selection):
                if self._is_in_collection(
                    sickchill.indexer.slug(cur_episode["indexer"]),
                    str(cur_episode["showid"]),
                    str(cur_episode["season"]),
                    str(cur_episode["episode"]),
                ):
                    if cur_episode["location"] == "":
                        logger.debug(
                            "Removing Episode {show} {ep} from collection".format(
                                show=cur_episode["show_name"], ep=episode_num(cur_episode["season"], cur_episode["episode"])
                            )
                        )
                        trakt_data.append(
                            (
                                cur_episode["showid"],
                                cur_episode["indexer"],
                                cur_episode["show_name"],
                                cur_episode["startyear"],
                                cur_episode["season"],
                                cur_episode["episode"],
                            )
                        )

            if trakt_data:
                try:
                    data = self._trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/collection/remove", data, method="POST")
                    self._get_shows_collection()
                except traktException as error:
                    logger.warning(f"Could not connect to Trakt service. Error: {error}")

            logger.debug("COLLECTION::REMOVE::FINISH - Look for Episodes to Remove From Trakt Collection")

    def _add_episodes_to_trakt_collection(self):
        if settings.TRAKT_SYNC and settings.USE_TRAKT:
            logger.debug("COLLECTION::ADD::START - Look for Episodes to Add to Trakt Collection")

            main_db_con = db.DBConnection()
            sql_selection = (
                "select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in ("
                + ",".join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED])
                + ")"
            )

            trakt_data = []

            for cur_episode in main_db_con.select(sql_selection):
                if not self._is_in_collection(
                    sickchill.indexer.slug(cur_episode["indexer"]),
                    str(cur_episode["showid"]),
                    str(cur_episode["season"]),
                    str(cur_episode["episode"]),
                ):
                    logger.debug(
                        "Adding Episode {show} {ep} to collection".format(
                            show=cur_episode["show_name"], ep=episode_num(cur_episode["season"], cur_episode["episode"])
                        )
                    )
                    trakt_data.append(
                        (
                            cur_episode["showid"],
                            cur_episode["indexer"],
                            cur_episode["show_name"],
                            cur_episode["startyear"],
                            cur_episode["season"],
                            cur_episode["episode"],
                        )
                    )

            if trakt_data:
                try:
                    data = self._trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/collection", data, method="POST")
                    self._get_shows_collection()
                except traktException as error:
                    logger.warning(f"Could not connect to Trakt service. Error: {error}")

            logger.debug("COLLECTION::ADD::FINISH - Look for Episodes to Add to Trakt Collection")

    def _sync_watchlists(self):
        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            logger.debug("Sync SickChill with Trakt Watchlist")

            self._remove_watched_shows_from_sickchill()

            if self._get_shows_watchlist():
                self._add_shows_to_trakt_watchlist()
                self._update_shows()

            if self._get_episode_watchlist():
                self._remove_episodes_from_trakt_watchlist()
                self._add_episodes_to_trakt_watchlist()
                self._update_episodes()

    def _remove_episodes_from_trakt_watchlist(self):
        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            logger.debug("WATCHLIST::REMOVE::START - Look for Episodes to Remove from Trakt Watchlist")

            main_db_con = db.DBConnection()
            sql_selection = "select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid"
            trakt_data = []

            for cur_episode in main_db_con.select(sql_selection):
                if self._is_in_epoisode_watchlist(
                    sickchill.indexer.slug(cur_episode["indexer"]), str(cur_episode["showid"]), str(cur_episode["season"]), str(cur_episode["episode"])
                ):
                    if cur_episode["status"] not in Quality.SNATCHED + Quality.SNATCHED_PROPER + [UNKNOWN] + [WANTED]:
                        logger.debug(
                            "Removing Episode {show} {ep} from watchlist".format(
                                show=cur_episode["show_name"], ep=episode_num(cur_episode["season"], cur_episode["episode"])
                            )
                        )
                        trakt_data.append(
                            (
                                cur_episode["showid"],
                                cur_episode["indexer"],
                                cur_episode["show_name"],
                                cur_episode["startyear"],
                                cur_episode["season"],
                                cur_episode["episode"],
                            )
                        )

            if trakt_data:
                try:
                    data = self._trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/watchlist/remove", data, method="POST")
                    self._get_episode_watchlist()
                except traktException as error:
                    logger.warning(f"Could not connect to Trakt service. Error: {error}")

            logger.debug("WATCHLIST::REMOVE::FINISH - Look for Episodes to Remove from Trakt Watchlist")

    def _add_episodes_to_trakt_watchlist(self):
        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            logger.debug("WATCHLIST::ADD::START - Look for Episodes to Add to Trakt Watchlist")

            main_db_con = db.DBConnection()
            sql_selection = (
                "select tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode from tv_episodes,tv_shows where tv_shows.indexer_id = tv_episodes.showid and tv_episodes.status in ("
                + ",".join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + [WANTED]])
                + ")"
            )

            trakt_data = []

            for cur_episode in main_db_con.select(sql_selection):
                if not self._is_in_epoisode_watchlist(
                    sickchill.indexer.slug(cur_episode["indexer"]), str(cur_episode["showid"]), str(cur_episode["season"]), str(cur_episode["episode"])
                ):
                    logger.debug(
                        "Adding Episode {show} {ep} to watchlist".format(
                            show=cur_episode["show_name"], ep=episode_num(cur_episode["season"], cur_episode["episode"])
                        )
                    )
                    trakt_data.append(
                        (
                            cur_episode["showid"],
                            cur_episode["indexer"],
                            cur_episode["show_name"],
                            cur_episode["startyear"],
                            cur_episode["season"],
                            cur_episode["episode"],
                        )
                    )

            if trakt_data:
                try:
                    data = self._trakt_bulk_data_generate(trakt_data)
                    self.trakt_api.traktRequest("sync/watchlist", data, method="POST")
                    self._get_episode_watchlist()
                except traktException as error:
                    logger.warning(f"Could not connect to Trakt service. Error {error}")

            logger.debug("WATCHLIST::ADD::FINISH - Look for Episodes to Add to Trakt Watchlist")

    def _add_shows_to_trakt_watchlist(self):
        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
            logger.debug("SHOW_WATCHLIST::ADD::START - Look for Shows to Add to Trakt Watchlist")

            trakt_data = []

            for show in settings.showList or []:
                if not self._is_in_show_watchlist(show.idxr.slug, str(show.indexerid), "0", "0"):
                    logger.debug("Adding Show: Indexer {0} {1} - {2} to Watchlist".format(show.idxr.name, str(show.indexerid), show.name))
                    show_element = {"title": show.name, "year": show.startyear, "ids": {show.idxr.slug: show.indexerid}}

                    trakt_data.append(show_element)

            if trakt_data:
                try:
                    data = {"shows": trakt_data}
                    self.trakt_api.traktRequest("sync/watchlist", data, method="POST")
                    self._get_shows_watchlist()
                except traktException as error:
                    logger.warning(f"Could not connect to Trakt service. Error: {error}")

            logger.debug("SHOW_WATCHLIST::ADD::FINISH - Look for Shows to Add to Trakt Watchlist")

    def _remove_watched_shows_from_sickchill(self):
        if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST and settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL:
            logger.debug("SHOW_SICKCHILL::REMOVE::START - Look for Shows to remove from SickChill")

            for show in settings.showList or []:
                if show.status in ("Ended", "Canceled"):
                    if not show.imdb_id:
                        logger.warning(
                            "Could not check trakt progress for {0} because the imdb id is missing from {1} data, skipping".format(show.name, show.idxr.name)
                        )
                        continue

                    try:
                        progress = self.trakt_api.traktRequest("shows/" + show.imdb_id + "/progress/watched") or {}
                    except traktException as error:
                        logger.warning(f"Could not connect to Trakt service. Aborting removing show {show.name} from SickChill. Error: {error}")
                        continue

                    if progress and progress.get("aired", True) == progress.get("completed", False):
                        settings.showQueueScheduler.action.remove_show(show, full=True)
                        logger.debug("Show: {0} has been removed from SickChill".format(show.name))

            logger.debug("SHOW_SICKCHILL::REMOVE::FINISH - Trakt Show Watchlist")

    def _update_shows(self):
        logger.debug("SHOW_WATCHLIST::CHECK::START - Trakt Show Watchlist")

        self._get_shows_watchlist()
        if not self.show_watchlist:
            logger.debug("No shows found in your watchlist, aborting watchlist update")
            return

        for index, indexer in sickchill.indexer:
            if indexer.slug in self.show_watchlist:
                for show_element in self.show_watchlist[indexer.slug]:
                    indexer_id = int(str(show_element))
                    show = self.show_watchlist[indexer.slug][show_element]

                    # logger.debug("Checking Show: %s %s %s" % (slug, indexer_id, show['title']))
                    if int(settings.TRAKT_METHOD_ADD) != 2:
                        self._add_show_with_defaults(index, indexer_id, show["title"], SKIPPED)
                    else:
                        self._add_show_with_defaults(index, indexer_id, show["title"], WANTED)

                    if int(settings.TRAKT_METHOD_ADD) == 1:
                        new_show = Show.find(settings.showList, indexer_id)

                        if new_show:
                            self._set_episode_to_wanted(new_show, 1, 1)
                        else:
                            self.wanted_episode_queue.append((indexer_id, 1, 1))

        logger.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Show Watchlist")

    def _update_episodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        logger.debug("SHOW_WATCHLIST::CHECK::START - Trakt Episode Watchlist")

        self._get_episode_watchlist()
        if not self.episode_watchlist:
            logger.debug("No episode found in your watchlist, aborting episode update")
            return

        managed_show = []

        for index, indexer in sickchill.indexer:
            if indexer.slug in self.episode_watchlist:
                for show_element in self.episode_watchlist[indexer.slug]:
                    indexer_id = int(show_element)
                    show = self.episode_watchlist[indexer.slug][show_element]

                    new_show = Show.find(settings.showList, indexer_id)

                    try:
                        if new_show:
                            if new_show.indexer == indexer:
                                for season_element in show["seasons"]:
                                    season = int(season_element)

                                    for episode_element in show["seasons"][season_element]["episodes"]:
                                        self._set_episode_to_wanted(new_show, season, int(episode_element))
                        else:
                            if indexer_id not in managed_show:
                                self._add_show_with_defaults(index, indexer_id, show["title"], SKIPPED)
                                managed_show.append(indexer_id)

                                for season_element in show["seasons"]:
                                    season = int(season_element)

                                    for episode_element in show["seasons"][season_element]["episodes"]:
                                        self.wanted_episode_queue.append((indexer_id, season, int(episode_element)))

                    except TypeError:
                        logger.debug("Could not parse the output from trakt for {0} ".format(show["title"]))
        logger.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Episode Watchlist")

    @staticmethod
    def _add_show_with_defaults(indexer, indexer_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not Show.find(settings.showList, int(indexer_id)):
            logger.info(f"Adding show {indexer_id}")
            root_dirs = settings.ROOT_DIRS.split("|")

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except Exception:
                location = None

            if location:
                showPath = os.path.join(location, sanitize_filename(name))
                dir_exists = helpers.makeDir(showPath)

                if not dir_exists:
                    logger.warning("Unable to create the folder {0} , can't add the show".format(showPath))
                    return
                else:
                    helpers.chmodAsParent(showPath)

                settings.showQueueScheduler.action.add_show(
                    int(indexer),
                    int(indexer_id),
                    showPath,
                    default_status=status,
                    quality=int(settings.QUALITY_DEFAULT),
                    season_folders=int(settings.SEASON_FOLDERS_DEFAULT),
                    paused=settings.TRAKT_START_PAUSED,
                    default_status_after=status,
                )
            else:
                logger.warning("There was an error creating the show, no root directory setting found")
                return

    def check_new_show(self, show):
        logger.debug("Checking if trakt watch list wants to search for episodes from new show " + show.name)
        for episode in self.wanted_episode_queue:
            if episode[0] != show.indexerid:
                continue

            self._set_episode_to_wanted(show, episode[1], episode[2])
            self.wanted_episode_queue.remove(episode)

    def _is_in_collection(self, slug, showid, season, episode):
        try:
            return self.collection_list[slug][showid]["seasons"][season]["episodes"][episode] == episode
        except (AttributeError, IndexError, KeyError):
            return False

    def _is_in_show_watchlist(self, slug, showid):
        try:
            return self.show_watchlist[slug][showid]["id"] == showid
        except (AttributeError, IndexError, KeyError):
            return False

    def _is_in_epoisode_watchlist(self, slug, showid, season, episode):
        try:
            self.episode_watchlist[slug][showid]["seasons"][season]["episodes"][episode] == episode
        except (AttributeError, IndexError, KeyError):
            return False

    def _get_shows_watchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """
        try:
            self.show_watchlist = {indexer.slug: {} for index, indexer in sickchill.indexer}
            trakt_show_watchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
            for slug in self.show_watchlist:
                for watchlist_element in trakt_show_watchlist:
                    if watchlist_element["show"]["ids"][slug]:
                        title = watchlist_element["show"]["title"]
                        year = str(watchlist_element["show"]["year"])

                        showid = str(watchlist_element["show"]["ids"][slug])
                        self.show_watchlist[slug][showid] = {"id": showid, "title": title, "year": year}
        except traktException as error:
            logger.warning(f"Could not connect to trakt service, cannot download Show Watchlist: {error}")
            return False
        return True

    def _get_episode_watchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """
        try:
            self.episode_watchlist = {indexer.slug: {} for index, indexer in sickchill.indexer}
            trakt_episode_watchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
            for slug in self.episode_watchlist:
                for watchlist_element in trakt_episode_watchlist:
                    if watchlist_element["show"]["ids"][slug]:
                        title = watchlist_element["show"]["title"]
                        year = str(watchlist_element["show"]["year"])
                        season = str(watchlist_element["episode"]["season"])
                        episode = str(watchlist_element["episode"]["number"])

                        showid = str(watchlist_element["show"]["ids"][slug])

                        if showid not in self.episode_watchlist[slug]:
                            self.episode_watchlist[slug][showid] = {"id": showid, "title": title, "year": year, "seasons": {}}

                        if season not in self.episode_watchlist[slug][showid]["seasons"]:
                            self.episode_watchlist[slug][showid]["seasons"][season] = {"s": season, "episodes": {}}

                        if episode not in self.episode_watchlist[slug][showid]["seasons"][season]["episodes"]:
                            self.episode_watchlist[slug][showid]["seasons"][season]["episodes"][episode] = episode

        except traktException as error:
            logger.warning(f"Could not connect to trakt service, cannot download Episode Watchlist: {error}")
            return False
        return True

    def _get_shows_collection(self):
        """
        Get Collection and parse once into addressable structure
        """
        try:
            self.collection_list = {indexer.slug: {} for index, indexer in sickchill.indexer}
            logger.debug("Getting Show Collection")
            trakt_collection_list = self.trakt_api.traktRequest("sync/collection/shows")
            for slug in self.collection_list:
                for watchlist_element in trakt_collection_list:
                    if "seasons" in watchlist_element:
                        for season_element in watchlist_element["seasons"]:
                            for episode_element in season_element["episodes"]:
                                season = str(season_element["number"])
                                episode = str(episode_element["number"])

                                if watchlist_element["show"]["ids"][slug]:
                                    title = watchlist_element["show"]["title"]
                                    year = str(watchlist_element["show"]["year"])
                                    showid = str(watchlist_element["show"]["ids"][slug])

                                    if showid not in self.collection_list[slug]:
                                        self.collection_list[slug][showid] = {"id": showid, "title": title, "year": year, "seasons": {}}

                                    if season not in self.collection_list[slug][showid]["seasons"]:
                                        self.collection_list[slug][showid]["seasons"][season] = {"s": season, "episodes": {}}

                                    if episode not in self.collection_list[slug][showid]["seasons"][season]["episodes"]:
                                        self.collection_list[slug][showid]["seasons"][season]["episodes"][episode] = episode
        except traktException as error:
            logger.warning(f"Could not connect to trakt service, cannot download Show Collection: {error}")
            return False
        return True

    @staticmethod
    def _trakt_bulk_data_generate(data):
        """
        Build the JSON structure to send back to Trakt
        """
        shows = {}
        seasons = {}

        for showid, indexer, show_name, startyear, season, episode in data:
            slug = sickchill.indexer.slug(indexer)
            if showid not in shows:
                shows[showid] = {"title": show_name, "year": startyear, "ids": {slug: showid}, "seasons": []}
                seasons[showid] = []

            if season not in seasons[showid]:
                seasons[showid].append(season)

        # build the query
        show_list = []
        seasons_list = {}

        for current_show in shows:
            seasons_list[current_show] = []

            for current_season in seasons[current_show]:
                episodes_list = []

                for showid, indexerid, show_name, startyear, season, episode in data:
                    if season == current_season and showid == current_show:
                        episodes_list.append({"number": episode})
                shows[current_show]["seasons"].append({"number": current_season, "episodes": episodes_list})
            show_list.append(shows[current_show])

        return {"shows": show_list}

    @staticmethod
    def _set_episode_to_wanted(show, season, episode):
        """
        Sets an episode to wanted, only if it is currently skipped
        """
        episode_object = show.getEpisode(season, episode)
        if episode_object:
            with episode_object.lock:
                if episode_object.status != SKIPPED or episode_object.airdate == datetime.date.min:
                    return

                logger.info("Setting episode {show} {ep} to wanted".format(show=show.name, ep=episode_num(season, episode)))
                # figure out what segment the episode is in and remember it, so we can backlog it

                episode_object.status = WANTED
                episode_object.saveToDB()

            cur_backlog_queue_item = search_queue.BacklogQueueItem(show, [episode_object])
            settings.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

            logger.info(
                "Starting backlog search for {show} {ep} because some episodes were set to wanted".format(show=show.name, ep=episode_num(season, episode))
            )
