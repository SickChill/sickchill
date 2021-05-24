import time
import traceback
from urllib.parse import urljoin

from requests.utils import add_dict_to_cookiejar

from sickchill import logger, settings
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import cpu_presets
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Demonoid")

        self.public = True
        self.minseed = 0
        self.sorting = None
        self.minleech = 0

        self.url = "https://demonoid.is"
        self.urls = {"RSS": urljoin(self.url, "rss.php"), "search": urljoin(self.url, "files/")}

        self.proper_strings = ["PROPER|REPACK"]

        self.cache_rss_params = {"category": 12, "quality": 58, "seeded": 0, "external": 2, "sort": "added", "order": "desc"}

        self.cache = DemonoidCache(self)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        # https://demonoid.is/files/?category=12&quality=58&seeded=0&external=2&sort=seeders&order=desc&query=SEARCH_STRING
        search_params = {
            "category": "12",  # 12: TV
            "seeded": 0,  # 0: True
            "external": 2,  # 0: Demonoid (Only works if logged in), 1: External, 2: Both
            "order": "desc",
            "sort": self.sorting or "seeders",
        }

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            if mode == "RSS":
                logger.info("Demonoid RSS search is not working through this provider yet, only string searches will work. Continuing")
                continue

            for search_string in {*search_strings[mode]}:
                search_params["query"] = search_string
                logger.debug("Search string: {0}".format(search_string))

                time.sleep(cpu_presets[settings.CPU_PRESET])

                data = self.get_url(self.urls["search"], params=search_params)
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                with BS4Parser(data, "html5lib") as html:
                    for result in html("img", alt="Download torrent"):
                        try:
                            data_row = result.find_parent("tr")
                            info_row = data_row.previous_sibling

                            data_cells = data_row("td")

                            e_title = info_row("td")[1]("a")[0]
                            e_download_links = data_cells[2]
                            e_file_size = data_cells[3]
                            e_seeders = data_cells[6]
                            e_leechers = data_cells[7]

                            title = e_title.get_text(strip=True)
                            details_url = e_title["href"]

                            if not (title and details_url):
                                if mode != "RSS":
                                    logger.debug("Discarding torrent because We could not parse the title and details")
                                continue

                            size = convert_size(e_file_size.get_text(strip=True)) or -1
                            seeders = try_int(e_seeders.get_text(strip=True))
                            leechers = try_int(e_leechers.get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            e_download_torrent, e_download_magnet = e_download_links("a")
                            download_url = urljoin(self.url, e_download_torrent["href"])
                            magnet = urljoin(self.url, e_download_magnet["href"])
                            torrent_hash = self.get_torrent_hash(details_url)

                            if not all([download_url, magnet, torrent_hash]):
                                logger.info(
                                    "Failed to get all required information from the details page. url:{}, magnet:{}, hash:{}".format(
                                        bool(download_url), bool(magnet), bool(torrent_hash)
                                    )
                                )
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": torrent_hash}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError, Exception):
                            logger.info(traceback.format_exc())
                            continue

                            # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

                results += items

            return results

    def get_torrent_hash(self, details_url):
        torrent_hash = None
        details_data = self.get_url(urljoin(self.url, details_url))
        if not details_data:
            logger.debug("No data returned from details page for result")
            return torrent_hash

        with BS4Parser(details_data, "html5lib") as html:
            torrent_hash = html("td", string="Torrent hash:")[0].parent("td")[1].get_text(strip=True).replace(" ", "")

        return torrent_hash


class DemonoidCache(tvcache.TVCache):
    def _get_rss_data(self):
        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit("=", 1) for x in self.provider.cookies.split(";")))

        return self.get_rss_feed(self.provider.urls["RSS"], self.provider.cache_rss_params)
