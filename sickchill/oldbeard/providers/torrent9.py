import re

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.FrenchProvider import FrenchTorrentProvider


class Provider(FrenchTorrentProvider):
    def __init__(self):
        super().__init__("Torrent9", "https://ww1.torrent9.re")

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                    search_url = self.url
                    post_data = {"torrentSearch": search_string}
                else:
                    search_url = self.url + "/torrents/series"
                    post_data = None

                data = self.get_url(search_url, post_data, returns="text")
                if not data:
                    continue

                with BS4Parser(data) as html:
                    for result in html.select("div.table-responsive tr"):
                        try:

                            link = result.select_one("a")
                            title = link.get_text(strip=False).replace("HDTV", "HDTV x264-Torrent9")
                            title = re.sub(r" Saison", " Season", title, flags=re.I)
                            download_url = self._retrieve_dllink_from_url(link.get("href"))
                            if not all([title, download_url]):
                                logger.debug(_("Could not find title and download url for result"))
                                continue

                            seeders = try_int(result.find(attrs={"src": re.compile(r".*.up\.jpg")}).parent.get_text(strip=True))
                            leechers = try_int(result.find(attrs={"src": re.compile(r".*.down\.jpg")}).parent.get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {title} (S:{seeders} L:{leechers})"
                                    )
                                continue

                            size = convert_size(result.find("td", text=re.compile(r"[\d0-9]* [KMG]B")).get_text(strip=True), -1) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug(f"Found result: {title} with {seeders} seeders and {leechers} leechers")

                            items.append(item)
                        except Exception as error:
                            logger.debug(f"Error parsing results {error}")
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
