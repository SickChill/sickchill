import re
import traceback

from sickchill import logger, settings
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("LimeTorrents")

        self.urls = {
            "index": "https://www.limetorrents.info/",
            "search": "https://www.limetorrents.info/searchrss/",
            "rss": "https://www.limetorrents.info/rss/tv/",
        }

        self.url = self.urls["index"]

        self.public = True
        self.minseed = 0
        self.minleech = 0

        self.proper_strings = ["PROPER", "REPACK", "REAL"]

        self.cache = tvcache.TVCache(self, search_params={"RSS": ["rss"]})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                try:
                    search_url = (self.urls["rss"], self.urls["search"] + search_string + "/")[mode != "RSS"]

                    data = self.get_url(search_url, returns="text")
                    if not data:
                        logger.debug("No data returned from provider")
                        continue

                    if not data.startswith("<?xml"):
                        logger.info("Expected xml but got something else, is your mirror failing?")
                        continue

                    with BS4Parser(data) as parser:
                        elements = parser("item")
                        if not elements:
                            logger.info("Returned xml contained no results")
                            continue

                        for item in elements:
                            try:
                                title = item.title.text
                                download_url = item.enclosure["url"]
                                torrent_hash = re.match(r"(.*)([A-F0-9]{40})(.*)", download_url, re.I).group(2)

                                if settings.TORRENT_METHOD != "blackhole" and "magnet:?" not in download_url:
                                    download_url = "magnet:?xt=urn:btih:" + torrent_hash + "&dn=" + title + self._custom_trackers

                                if not (title and download_url):
                                    continue

                                # seeders and leechers are presented diferently when doing a search and when looking for newly added
                                if mode == "RSS":
                                    # <![CDATA[
                                    # Category: <a href="http://www.limetorrents.info/browse-torrents/TV-shows/">TV shows</a><br /> Seeds: 1<br />Leechers: 0<br />Size: 7.71 GB<br /><br /><a href="http://www.limetorrents.info/Owen-Hart-of-Gold-Djon91-torrent-7180661.html">More @ limetorrents.info</a><br />
                                    # ]]>
                                    description = item.find("description")
                                    seeders = try_int(description("br")[0].next_sibling.strip().lstrip("Seeds: "))
                                    leechers = try_int(description("br")[1].next_sibling.strip().lstrip("Leechers: "))
                                else:
                                    # <description>Seeds: 6982 , Leechers 734</description>
                                    description = item.find("description").text.partition(",")
                                    seeders = try_int(description[0].lstrip("Seeds: ").strip())
                                    leechers = try_int(description[2].lstrip("Leechers ").strip())

                                torrent_size = item.find("size").text

                                size = convert_size(torrent_size) or -1

                            except (AttributeError, TypeError, KeyError, ValueError):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {title} (S:{seeders} L:{leechers})"
                                    )
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": torrent_hash}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.exception("Failed parsing provider. Traceback: {0!r}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
