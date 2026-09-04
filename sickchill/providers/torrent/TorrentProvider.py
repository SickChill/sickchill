from datetime import datetime

import bencode

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.db import DBConnection
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.result_classes import Proper, TorrentSearchResult
from sickchill.show.History import History
from sickchill.show.Show import Show

# Cap live proper episode searches per provider per ProperFinder run (Phase 1)
_LIVE_PROPER_EPISODE_CAP = 25


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        super().__init__(name)
        self.ratio = None
        self.provider_type = GenericProvider.TORRENT

    def find_propers(self, search_date=None):
        """Cache-first propers; live search only if cache is empty (bounded episode cap)."""
        results = []
        seen_urls = set()

        # Prefer TV cache (filled by daily RSS / update_cache) — titles keep PROPER/REPACK/REAL
        try:
            for row in self.cache.list_propers(search_date) or []:
                proper = Proper(row["name"], row["url"], datetime.fromtimestamp(row["time"], tz=sc_timezone), self.show)
                if proper.url and proper.url not in seen_urls:
                    seen_urls.add(proper.url)
                    results.append(proper)
        except Exception as error:
            logger.debug(f"{self.name}: cache list_propers failed during proper search: {error}")

        if results:
            logger.debug(f"{self.name}: using {len(results)} cached proper(s); skipping live proper search")
            return results

        # Fallback: one OR'd proper term per episode, capped
        add_string = self.proper_search_add_string()
        live_count = 0
        for show, episode in self._recent_proper_candidates(search_date):
            if live_count >= _LIVE_PROPER_EPISODE_CAP:
                logger.debug(f"{self.name}: live proper search capped at {_LIVE_PROPER_EPISODE_CAP} episodes")
                break
            self.current_episode_object = episode
            live_count += 1
            for search_string in self.get_episode_search_strings(episode, add_string=add_string):
                for item in self.search(search_string):
                    title, url = self._get_title_and_url(item)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append(Proper(title, url, sc_now(), show))

        if live_count:
            logger.debug(f"{self.name}: live proper searches for {live_count} episode(s); results={len(results)}")
        return results

    @staticmethod
    def _recent_proper_candidates(search_date=None):
        """
        Episodes recently snatched/downloaded that are not yet proper.

        Prefer history in the proper-search window over every aired ep in the last N days.
        """
        if search_date is None:
            search_date = sc_now()
        status_quality_list = Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST
        history_actions = Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST
        ep_placeholders = ", ".join(["?"] * len(status_quality_list))
        hist_placeholders = ", ".join(["?"] * len(history_actions))
        history_since = search_date.strftime(History.date_format)

        db = DBConnection()
        sql_results = db.select(
            f"""
            SELECT DISTINCT e.showid, e.season, e.episode, MAX(h.date) AS last_hist
            FROM tv_episodes AS e
            INNER JOIN history AS h
                ON h.showid = e.showid AND h.season = e.season AND h.episode = e.episode
            WHERE e.is_proper = 0
              AND e.status IN ({ep_placeholders})
              AND h.action IN ({hist_placeholders})
              AND h.date >= ?
            GROUP BY e.showid, e.season, e.episode
            ORDER BY last_hist DESC
            LIMIT ?
            """,
            [*status_quality_list, *history_actions, history_since, _LIVE_PROPER_EPISODE_CAP],
        )

        for result in sql_results or []:
            show = Show.find(settings.show_list, int(result["showid"]))
            if not show:
                continue
            episode = show.get_episode(result["season"], result["episode"])
            if episode:
                yield show, episode

    @property
    def is_active(self):
        return bool(settings.USE_TORRENTS) and self.is_enabled

    @property
    def _custom_trackers(self):
        if not (settings.TRACKERS_LIST and self.public):
            return ""

        return "&tr=" + "&tr=".join({x.strip() for x in settings.TRACKERS_LIST.split(",") if x.strip()})

    def _get_result(self, episodes, provider, url):
        return TorrentSearchResult(episodes, provider, url)

    def _get_size(self, item):
        if isinstance(item, dict):
            size = item.get("size", -1)
        elif isinstance(item, (list, tuple)) and len(item) > 2:
            size = item[2]
        else:
            size = -1

        size = try_int(size, -1)

        # Make sure we didn't select seeds/leechers by accident
        if not size or size < 1024 * 1024:
            size = -1

        return size

    def _get_storage_dir(self):
        return settings.TORRENT_DIR

    def _get_title_and_url(self, item):
        if isinstance(item, dict):
            download_url = item.get("url", "")
            title = item.get("title", "")

            if not download_url:
                download_url = item.get("link", "")
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            download_url = item[1]
            title = item[0]
        else:
            download_url = ""
            title = ""

        if title.endswith("DIAMOND"):
            logger.info("Skipping DIAMOND release for mass fake releases.")
            download_url = title = "FAKERELEASE"

        if download_url:
            download_url = download_url.replace("&amp;", "&")

        if title:
            title = title.replace(" ", ".")

        return title, download_url

    def _verify_download(self, filename):
        try:
            bencode.bread(filename)
        except bencode.BencodeDecodeError as error:
            logger.debug(f"Failed to validate torrent file: {error}")
            logger.debug("Result is not a valid torrent file")
            return False
        return True

    def seed_ratio(self):
        return self.ratio
