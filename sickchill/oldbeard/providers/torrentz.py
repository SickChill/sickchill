import re
import traceback
from urllib.parse import urljoin

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("Torrentz")

        # Credentials
        self.public = True

        # Feed verified does not exist on this clone
        # self.confirmed = True

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://torrentz.com/"
        self.urls = {
            "verified": urljoin(self.url, "feed_verified"),
            "feed": urljoin(self.url, "feed"),
            "base": self.url,
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, min_time=15)  # only poll Torrentz every 15 minutes max

    @staticmethod
    def _split_description(description):
        match = re.findall(r"[0-9]+", description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in {*search_strings[mode]}:

                # Feed verified does not exist on this clone
                # search_url = self.urls['verified'] if self.confirmed else self.urls['feed']
                search_url = self.urls["feed"]
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                data = self.get_url(search_url, params={"f": search_string}, returns="text")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                if not data.startswith("<?xml"):
                    logger.info("Expected xml but got something else, is your mirror failing?")
                    continue

                try:
                    with BS4Parser(data, "html5lib") as parser:
                        for item in parser("item"):
                            if item.category and "tv" not in item.category.get_text(strip=True).lower():
                                continue

                            title = item.title.get_text(strip=True)
                            t_hash = item.guid.get_text(strip=True).rsplit("/", 1)[-1]

                            if not all([title, t_hash]):
                                continue

                            download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + self._custom_trackers
                            torrent_size, seeders, leechers = self._split_description(item.find("description").text)
                            size = convert_size(torrent_size) or -1

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            result = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": t_hash}
                            items.append(result)
                except Exception:
                    logger.exception("Failed parsing provider. Traceback: {0!r}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
