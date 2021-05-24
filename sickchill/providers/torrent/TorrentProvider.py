from datetime import datetime

import bencodepy
from feedparser import FeedParserDict

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard.classes import Proper, TorrentSearchResult
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.db import DBConnection
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.show.Show import Show


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        super().__init__(name)
        self.ratio = None
        self.provider_type = GenericProvider.TORRENT

    def find_propers(self, search_date=None):
        results = []
        db = DBConnection()
        placeholders = ", ".join(["?"] * len(Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST))
        sql_results = db.select(
            f"SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) WHERE e.airdate >= ? AND e.status IN ({placeholders}) and e.is_proper = 0",
            [search_date.toordinal(), *Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST],
        )

        for result in sql_results or []:
            show = Show.find(settings.showList, int(result["showid"]))

            if show:
                episode = show.getEpisode(result["season"], result["episode"])

                for term in self.proper_strings:
                    search_strings = self.get_episode_search_strings(episode, add_string=term)

                    for search_string in search_strings:
                        for item in self.search(search_string):
                            title, url = self._get_title_and_url(item)

                            results.append(Proper(title, url, datetime.today(), show))

        return results

    @property
    def is_active(self):
        return bool(settings.USE_TORRENTS) and self.is_enabled

    @property
    def _custom_trackers(self):
        if not (settings.TRACKERS_LIST and self.public):
            return ""

        return "&tr=" + "&tr=".join({x.strip() for x in settings.TRACKERS_LIST.split(",") if x.strip()})

    def _get_result(self, episodes):
        return TorrentSearchResult(episodes)

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
        if isinstance(item, (dict, FeedParserDict)):
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
            bencodepy.bread(filename)
        except bencodepy.BencodeDecodeError as e:
            logger.debug("Failed to validate torrent file: {0}".format(str(e)))
            logger.debug("Result is not a valid torrent file")
            return False
        return True

    def seed_ratio(self):
        return self.ratio
