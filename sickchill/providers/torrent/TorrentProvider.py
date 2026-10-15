from datetime import datetime

import bencode

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.db import DBConnection
from sickchill.oldbeard.helpers import release_matches_fingerprint, split_release_fingerprint
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.result_classes import Proper, TorrentSearchResult
from sickchill.show.History import History
from sickchill.show.Show import Show

# Cap live proper searches per provider per ProperFinder run
_LIVE_PROPER_SEASON_CAP = 25
# Candidate SQL still bounds episodes in the proper-search window
_LIVE_PROPER_EPISODE_CAP = 25


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        super().__init__(name)
        self.ratio = None
        self.provider_type = GenericProvider.TORRENT

    def find_propers(self, search_date=None):
        """Match PROPER/REPACK/REAL against history.resource fingerprints, then live-search those."""
        results = []
        seen_urls = set()
        candidates = []
        for show, episode, resource in self._recent_proper_candidates(search_date):
            anime = bool(getattr(show, "is_anime", False) or getattr(show, "anime", False))
            fingerprint = split_release_fingerprint(resource, anime=anime)
            if fingerprint is None or fingerprint.is_proper:
                continue
            candidates.append((show, episode, fingerprint))

        if not candidates:
            return results

        season_pack_keys = self._shared_season_pack_keys(candidates)
        try:
            for row in self.cache.list_propers(search_date) or []:
                title = row["name"] or ""
                url = row["url"] or ""
                if not url or url in seen_urls:
                    continue
                matched_show = self._cache_title_matches_candidates(title, candidates, season_pack_keys)
                if matched_show:
                    seen_urls.add(url)
                    results.append(Proper(title, url, datetime.fromtimestamp(row["time"], tz=sc_timezone), matched_show))
        except Exception as error:
            logger.debug(f"{self.name}: cache list_propers failed during proper search: {error}")

        if self.is_rate_limited():
            logger.debug(f"{self.name}: skipping live proper search (provider rate limited)")
            return results

        live_count = 0
        for show, episode, fingerprint, season_pack in self._live_proper_search_plan(candidates, season_pack_keys):
            if self.is_rate_limited():
                logger.debug(f"{self.name}: stopping live proper searches after rate limit")
                break
            if live_count >= _LIVE_PROPER_SEASON_CAP:
                logger.debug(f"{self.name}: live proper search capped at {_LIVE_PROPER_SEASON_CAP} searches")
                break
            search_string = self._live_proper_search_string(show, episode, fingerprint, season_pack=season_pack)
            if not search_string:
                continue
            self.show = show
            self.current_episode_object = episode
            live_count += 1
            for item in self.search(search_string):
                title, url = self._get_title_and_url(item)
                if not url or url in seen_urls:
                    continue
                anime = bool(getattr(show, "is_anime", False) or getattr(show, "anime", False))
                if not release_matches_fingerprint(title, fingerprint, require_episode=not season_pack, anime=anime):
                    continue
                seen_urls.add(url)
                results.append(Proper(title, url, sc_now(), show))

        if live_count:
            logger.debug(f"{self.name}: live proper searches for {live_count} query(ies); results={len(results)}")
        return results

    @staticmethod
    def _shared_season_pack_keys(candidates):
        """Seasons where every history fingerprint shares quality + remainder (2+ episodes)."""
        grouped: dict[tuple, list] = {}
        for show, episode, fingerprint in candidates:
            grouped.setdefault((show.indexerid, episode.season), []).append(fingerprint)
        shared = set()
        for key, fingerprints in grouped.items():
            if len(fingerprints) < 2:
                continue
            remainders = {fingerprint.remainder for fingerprint in fingerprints}
            qualities = {fingerprint.quality for fingerprint in fingerprints}
            if len(remainders) == 1 and len(qualities) == 1:
                shared.add(key)
        return shared

    @staticmethod
    def _cache_title_matches_candidates(title, candidates, season_pack_keys):
        for show, episode, fingerprint in candidates:
            anime = bool(getattr(show, "is_anime", False) or getattr(show, "anime", False))
            if release_matches_fingerprint(title, fingerprint, anime=anime):
                return show
            key = (show.indexerid, episode.season)
            if key in season_pack_keys and release_matches_fingerprint(title, fingerprint, require_episode=False, anime=anime):
                return show
        return None

    @staticmethod
    def _live_proper_search_plan(candidates, season_pack_keys):
        """Season-pack query first when suffixes match, then one query per episode."""
        emitted_season = set()
        for show, episode, fingerprint in candidates:
            key = (show.indexerid, episode.season)
            if key in season_pack_keys and key not in emitted_season:
                emitted_season.add(key)
                season_fp = fingerprint._replace(episode=None, episode_tag=f"S{int(episode.season):02d}")
                yield show, episode, season_fp, True
            yield show, episode, fingerprint, False

    def _live_proper_search_string(self, show, episode, fingerprint, season_pack=False) -> dict | None:
        """Same search-string builder as daily/backlog, plus quality token and proper_strings."""
        if not show or not episode or not fingerprint:
            return None
        add_string = " ".join(part for part in (fingerprint.quality_token, self.proper_search_add_string()) if part)
        self.show = show
        self.current_episode_object = episode
        if season_pack:
            search_strings = {}
            for block in self.get_season_search_strings(episode):
                for mode, values in block.items():
                    search_strings.setdefault(mode, set())
                    for value in values:
                        query = f"{value} {add_string}".strip() if add_string else value
                        logger.debug(f"{self.name}: live proper search: {query}")
                        search_strings[mode].add(query)
            return search_strings or None
        search_strings = {}
        for block in self.get_episode_search_strings(episode, add_string=add_string):
            for mode, values in block.items():
                search_strings.setdefault(mode, set()).update(values)
                for value in values:
                    logger.debug(f"{self.name}: live proper search: {value}")
        return search_strings or None

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
            SELECT h.showid, h.season, h.episode, h.resource, h.date
            FROM history AS h
            INNER JOIN tv_episodes AS e
                ON h.showid = e.showid AND h.season = e.season AND h.episode = e.episode
            WHERE e.is_proper = 0
              AND e.status IN ({ep_placeholders})
              AND h.action IN ({hist_placeholders})
              AND h.date >= ?
            ORDER BY h.date DESC
            """,
            [*status_quality_list, *history_actions, history_since],
        )

        seen_episodes = set()
        yielded = 0
        for result in sql_results or []:
            episode_key = (int(result["showid"]), int(result["season"]), int(result["episode"]))
            if episode_key in seen_episodes:
                continue
            seen_episodes.add(episode_key)
            resource = result["resource"] or ""
            show = Show.find(settings.show_list, int(result["showid"]))
            if not show:
                continue
            episode = show.get_episode(result["season"], result["episode"])
            if not episode:
                continue
            yield show, episode, resource
            yielded += 1
            if yielded >= _LIVE_PROPER_EPISODE_CAP:
                break

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
