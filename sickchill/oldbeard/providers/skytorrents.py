from urllib.parse import urljoin

import validators

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("SkyTorrents")

        self.public = True

        self.minseed = 0
        self.minleech = 0

        self.url = "https://www.skytorrents.org"
        # https://www.skytorrents.org/?query=arrow&category=show&tag=hd&sort=seeders&type=video
        # https://www.skytorrents.org/top100?category=show&type=video&sort=created
        self.urls = {"search": urljoin(self.url, "/"), "rss": urljoin(self.url, "/top100")}

        self.custom_url = None

        self.cache = tvcache.TVCache(self, search_params={"RSS": [""]})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                search_url = (self.urls["search"], self.urls["rss"])[mode == "RSS"]
                if self.custom_url:
                    if validators.url(self.custom_url) != True:
                        logger.warning("Invalid custom url: {0}".format(self.custom_url))
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                if mode != "RSS":
                    search_params = {"search": search_string, "sort": ("seeders", "created")[mode == "RSS"]}
                else:
                    search_params = {"category": "show", "type": "video", "sort": "created"}

                data = self.get_url(search_url, params=search_params, returns="text")
                if not data:
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                with BS4Parser(data, "html5lib") as html:
                    labels = [label.get_text(strip=True) for label in html("th")]
                    for item in html("tr", attrs={"data-size": True}):
                        try:
                            size = try_int(item["data-size"])
                            cells = item.find_all("td")

                            title_block_links = cells[labels.index("Name")].find_all("a")
                            title = title_block_links[0].get_text(strip=True)
                            info_hash = title_block_links[0]["href"].split("/")[1]
                            download_url = title_block_links[2]["href"]

                            seeders = try_int(cells[labels.index("Seeders")].get_text(strip=True))
                            leechers = try_int(cells[labels.index("Leechers")].get_text(strip=True))

                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": info_hash}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
