import re
import urllib.parse
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import subliminal

from sickchill import logger, settings
from sickchill.helper.metaclasses import Singleton
from sickchill.oldbeard.classes import SearchResult

if TYPE_CHECKING:
    from sickchill.tv import TVEpisode, TVShow
    from sickchill.oldbeard.subtitles import Scores
    from sickchill.providers.GenericProvider import GenericProvider

from sickchill.helper.common import remove_extension, try_int
from sickchill.helper.exceptions import EpisodeNotFoundException
from sickchill.oldbeard.common import FAILED, Quality, SNATCHED, SUBTITLED, WANTED
from sickchill.oldbeard.db import DBConnection


class History(object, metaclass=Singleton):
    date_format = "%Y%m%d%H%M%S"

    def __init__(self):
        self.db: DBConnection = DBConnection()  # DataSource: sickchill.db
        self.failed_db: DBConnection = DBConnection("failed.db")  # DataSource: failed.db

        self.trim()

    def remove(self, items):
        """
        Removes the selected history
        :param items: Contains the properties of the log entries to remove
        """
        query = ""

        params = []
        for item in items:
            if query:
                query += " OR "

            query += "(date IN (?) AND showid = ? AND season = ? AND episode = ?)"
            params.extend([",".join(item["dates"]), item["show_id"], item["season"], item["episode"]])

        self.db.action("DELETE FROM history WHERE " + query, params)

    def clear(self):
        """
        Clear all the history
        """
        # noinspection SqlWithoutWhere
        self.db.action("DELETE FROM history")

    def get(self, limit: int = 100, action: str = None):
        """
        :param limit: The maximum number of elements to return
        :param action: The type of action to filter in the history. Either 'downloaded' or 'snatched'. Anything else or
                        no value will return everything (up to ``limit``)
        :return: The last ``limit`` elements of type ``action`` in the history
        """

        action = action.lower() if isinstance(action, str) else ""

        if action == "downloaded":
            actions = Quality.DOWNLOADED
        elif action == "snatched":
            actions = Quality.SNATCHED
        else:
            actions = Quality.DOWNLOADED + Quality.SNATCHED

        limit = max(try_int(limit, 0), 0)

        # DataSource: sickchill.db
        common_sql = (
            "SELECT action, date, episode, provider, h.quality, resource, season, show_name, showid "
            "FROM history h, tv_shows s "
            "WHERE h.showid = s.indexer_id "
        )  # DataSource: sickchill.db
        replacements = ",".join(["?"] * len(actions))
        filter_sql = f"AND action IN ({replacements})"
        order_sql = "ORDER BY date DESC "

        if limit == 0:
            if actions:
                results = self.db.select(common_sql + filter_sql + order_sql, actions)
            else:
                results = self.db.select(common_sql + order_sql)
        else:
            if actions:
                results = self.db.select(common_sql + filter_sql + order_sql + "LIMIT ?", actions + [limit])
            else:
                results = self.db.select(common_sql + order_sql + "LIMIT ?", [limit])

        data = []
        for result in results:
            data.append(
                {
                    "action": result["action"],
                    "date": result["date"],
                    "episode": result["episode"],
                    "provider": result["provider"],
                    "quality": result["quality"],
                    "resource": result["resource"],
                    "season": result["season"],
                    "show_id": result["showid"],
                    "show_name": result["show_name"],
                }
            )

        return data

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """
        back_thirty_days = (datetime.today() - timedelta(days=30)).strftime(self.date_format)
        self.db.action("DELETE FROM history WHERE date < ?", [back_thirty_days])
        if settings.USE_FAILED_DOWNLOADS:
            self.failed_db.action("DELETE FROM history WHERE date < ?", [back_thirty_days])

    def _log_history_item(self, action: int, showid: int, season: int, episode: int, quality: int, resource: str, provider, version=-1):
        """
        Insert a history item in DB

        :param action: action taken (snatch, download, etc)
        :param showid: showid this entry is about
        :param season: show season
        :param episode: show episode
        :param quality: media quality
        :param resource: resource used
        :param provider: provider used
        :param version: tracked version of file (defaults to -1)
        """
        # DataSource: sickchill.db
        return self.db.action(
            "INSERT INTO history (action, date, showid, season, episode, quality, resource, provider, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [action, datetime.today().strftime(self.date_format), showid, season, episode, quality, resource, provider, version],
        )

    def log_snatch(self, result: SearchResult):
        """
        Log history of snatch

        :param result: search result object
        """
        provider_class: "GenericProvider" = result.provider
        show: "TVShow" = result.episodes[0].show
        if provider_class:
            provider = provider_class.name
        else:
            provider = "unknown"

        for episode in result.episodes:
            self._log_history_item(
                Quality.compositeStatus(SNATCHED, result.quality),
                episode.show.indexerid,
                episode.season,
                episode.episode,
                result.quality,
                result.name,
                provider,
                result.version,
            )
            if settings.USE_FAILED_DOWNLOADS:
                self.failed_db.action(
                    'INSERT INTO history (date, size, "release", provider, showid, season, episode, old_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    [
                        datetime.today().strftime(self.date_format),
                        result.size,
                        self.prepare_failed_name(result.name),
                        provider,
                        show.indexerid,
                        episode.season,
                        episode.episode,
                        episode.status,
                    ],
                )

    def log_download(self, episode: "TVEpisode", filename: str, quality: int, group: str = None, version: int = -1):
        """
        Log history of download

        :param episode: episode of show
        :param filename: file on disk where the download is
        :param quality: Quality of download
        :param group: Release group
        :param version: Version of file (defaults to -1)
        """
        self._log_history_item(episode.status, episode.show.indexerid, episode.season, episode.episode, quality, filename, group or -1, version)

    def log_subtitle(self, show: int, season: int, episode: int, status: int, subtitle: subliminal.subtitle.Subtitle, scores: "Scores"):
        """
        Log download of subtitle

        :param show: Showid of download
        :param season: Show season
        :param episode: Show episode
        :param status: Status of download
        :param subtitle: Result object
        :param scores: Scores named tuple
        """
        if settings.SUBTITLES_HISTORY:
            logger.debug(
                f"[{subtitle.provider_name}] Subtitle score for {subtitle.id} is: {scores.res}/{scores.percent}% (min={scores.min}/{scores.min_percent})"
            )
            status, quality = Quality.splitCompositeStatus(status)
            self._log_history_item(
                Quality.compositeStatus(SUBTITLED, quality), show, season, episode, quality, subtitle.language.opensubtitles, subtitle.provider_name
            )

    def log_failed(self, episode_object: "TVEpisode", release: str, provider: str = ""):
        """
        Log a failed download

        :param episode_object: Episode object
        :param release: Release group
        :param provider: Provider used for snatch
        """

        status, quality = Quality.splitCompositeStatus(episode_object.status)
        self._log_history_item(
            Quality.compositeStatus(FAILED, quality), episode_object.show.indexerid, episode_object.season, episode_object.episode, quality, release, provider
        )

        if not settings.USE_FAILED_DOWNLOADS:
            return

        size = -1

        release = self.prepare_failed_name(release)

        sql_results = self.failed_db.select('SELECT * FROM history WHERE "release" = ?', [release])

        if not sql_results:
            logger.warning("Release not found in snatch history.")
        elif len(sql_results) > 1:
            logger.warning("Multiple logged snatches found for release")
            num_sizes = len(set(x["size"] for x in sql_results))
            providers = len(set(x["provider"] for x in sql_results))
            if num_sizes == 1:
                logger.warning("However, they're all the same size. Continuing with found size.")
                size = sql_results[0]["size"]
            else:
                logger.warning("They also vary in size. Deleting the logged snatches and recording this release with no size/provider")
                for result in sql_results:
                    self.remove_snatch(result["release"], result["size"], result["provider"])

            if providers == 1:
                logger.info("They're also from the same provider. Using it as well.")
                provider = sql_results[0]["provider"]
        else:
            size = sql_results[0]["size"]
            provider = sql_results[0]["provider"]

        if not self.has_failed(release, size, provider):
            self.failed_db.action('INSERT INTO failed ("release", size, provider) VALUES (?, ?, ?)', [release, size, provider])

        self.remove_snatch(release, size, provider)

    @staticmethod
    def prepare_failed_name(release: str):
        """Standardizes release name for failed DB"""

        fixed = urllib.parse.unquote(release)
        if fixed.endswith((".nzb", ".torrent")):
            fixed = remove_extension(fixed)

        return re.sub(r"[.\-+ ]", "_", fixed)

    def log_success(self, release):
        self.failed_db.action('DELETE FROM history WHERE "release" = ?', [self.prepare_failed_name(release)])

    def has_failed(self, release: str, size: int, provider: str = "%"):
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

        return bool(
            self.failed_db.select_one(
                'SELECT "release" FROM failed WHERE "release" = ? AND size = ? AND provider LIKE ? ', [self.prepare_failed_name(release), size, provider]
            )
        )

    def revert_episode(self, episode_object: "TVEpisode"):
        """Restore the episodes of a failed download to their original state"""
        if not settings.USE_FAILED_DOWNLOADS:
            return

        sql_results = self.failed_db.select(
            "SELECT episode, old_status FROM history WHERE showid = ? AND season = ?", [episode_object.show.indexerid, episode_object.season]
        )

        history_eps = {res["episode"]: res for res in sql_results}

        try:
            logger.info(f"Reverting episode ({episode_object.season}, {episode_object.episode}): {episode_object.episode}")
            with episode_object.lock:
                if episode_object.episode in history_eps:
                    logger.info("Found in history")
                    episode_object.status = history_eps[episode_object.episode]["old_status"]
                else:
                    logger.debug("Episode don't have a previous snatched status to revert. Setting it back to WANTED")
                    episode_object.status = WANTED
                    episode_object.save_to_db()

        except EpisodeNotFoundException as error:
            logger.warning(f"Unable to create episode, please set its status manually: {error}")

    def mark_failed(self, episode_object: "TVEpisode"):
        """
        Mark an episode_object as failed

        :param episode_object: Episode object to mark as failed
        :return: empty string
        """
        if not settings.USE_FAILED_DOWNLOADS:
            return

        logger.info(f"Marking episode as bad: [{episode_object.pretty_name}]")
        try:
            with episode_object.lock:
                quality = Quality.splitCompositeStatus(episode_object.status)[1]
                episode_object.status = Quality.compositeStatus(FAILED, quality)
                episode_object.save_to_db()

        except EpisodeNotFoundException as error:
            logger.warning(f"Unable to get episode, please set its status manually: {error}")

        (release, provider) = self.find_release(episode_object)
        if release:
            self.log_failed(episode_object, release, provider)

        self.revert_episode(episode_object)

    def remove_snatch(self, release: str, size: int, provider: str):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """
        self.failed_db.action('DELETE FROM history WHERE "release" = ? AND size = ? AND provider = ?', [self.prepare_failed_name(release), size, provider])

    def find_release(self, episode_object: "TVEpisode"):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        # Clear old snatches for this release if any exist
        # self.failed_db.action(
        #     "DELETE FROM history WHERE showid = {0} AND season = {1} AND episode = {2}"
        #     " AND date < (SELECT max(date) FROM history WHERE showid = {0} AND season = {1} AND episode = {2})".format
        #     (episode_object.show.indexerid, episode_object.season, episode_object.episode)
        # )

        # Search for release in snatch history
        results = self.failed_db.select(
            'SELECT "release", provider, date FROM history WHERE showid = ? AND season = ? AND episode = ?',
            [episode_object.show.indexerid, episode_object.season, episode_object.episode],
        )

        for result in results:
            release = str(result["release"])
            provider = str(result["provider"])
            date = result["date"]

            # Clear any incomplete snatch records for this release if any exist
            self.failed_db.action('DELETE FROM history WHERE "release" = ? AND date <> ?', [release, date])

            # Found a previously failed release
            logger.debug(f"Failed release found for season ({episode_object.season}): ({result['release']})")
            return release, provider

        # Release was not found
        logger.debug(f"No releases found for season ({episode_object.season}) of ({episode_object.show.indexerid})")
        return None, None
