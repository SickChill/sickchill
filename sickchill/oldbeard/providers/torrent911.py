import re

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.FrenchProvider import FrenchTorrentProvider


class Provider(FrenchTorrentProvider):
    def __init__(self):
        super().__init__("Torrent911", "https://www.torrent911.tv")

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                    search_url = self.url + "/recherche/" + search_string
                else:
                    search_url = self.url + "/torrents/series/date/desc"

                data = self.get_url(search_url, returns="text")
                if not data:
                    continue

                with BS4Parser(data) as html:
                    # Skip column headers
                    for result in html.select("table.table-hover tr")[1:]:
                        try:
                            title = result.select_one(".maxi").get_text(strip=True).replace("HDTV", "HDTV x264-Torrent911")
                            title = re.sub(r" Saison", " Season", title, flags=re.I)
                            download_url = self._retrieve_dllink_from_url(result.select_one("a").get("href"))
                            if not all([title, download_url]):
                                logger.debug(_("Could not find title and download url for result"))
                                continue

                            seeders = try_int(result.find(attrs={"src": re.compile(r".*.uploader\.png")}).parent.get_text(strip=True))
                            leechers = try_int(result.find(attrs={"src": re.compile(r".*.downloader\.png")}).parent.get_text(strip=True))
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
