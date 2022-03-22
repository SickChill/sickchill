from urllib.parse import urljoin

import validators
from markdown2 import _slugify as slugify

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("MagnetDL")

        self.minseed = 0
        self.minleech = 0

        self.url = "https://www.magnetdl.com"
        self.urls = {"rss": urljoin(self.url, "download/tv/age/desc/")}

        self.custom_url = None
        self.headers.update({"Accept": "application/html"})

        self.cache = tvcache.TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))
                    search = slugify(search_string)
                    search_url = urljoin(self.url, "{}/{}/".format(search[0], search))
                else:
                    search_url = self.urls["rss"]

                if self.custom_url:
                    if validators.url(self.custom_url) != True:
                        logger.warning("Invalid custom url: {0}".format(self.custom_url))
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                data = self.get_url(search_url, returns="text")
                if not data:
                    logger.debug("URL did not return results/data, if the results are on the site maybe try a custom url, or a different one")
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", class_="download")
                    torrent_body = torrent_table.find("tbody") if torrent_table else []
                    # noinspection PyCallingNonCallable
                    torrent_rows = torrent_body("tr") if torrent_body else []

                    # Continue only if at least one Release is found
                    if not torrent_rows:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    labels = [x.get_text(strip=True) for x in torrent_table.find("thead").find("tr")("th")]

                    # Skip column headers
                    for result in torrent_rows[0:-1:2]:
                        try:
                            if len(result("td")) < len(labels):
                                continue

                            title = result.find("td", class_="n").find("a")["title"]
                            magnet = result.find("td", class_="m").find("a")["href"]
                            seeders = try_int(result.find("td", class_="s").get_text(strip=True))
                            leechers = try_int(result.find("td", class_="l").get_text(strip=True))
                            size = convert_size(result("td")[labels.index("Size")].get_text(strip=True) or "") or -1

                            if not all([title, magnet]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the"
                                        " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                    )
                                continue

                            item = {"title": title, "link": magnet + self._custom_trackers, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception as e:
                            continue

                # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: d.get("seeders", 0), reverse=True)
                results += items

            return results
