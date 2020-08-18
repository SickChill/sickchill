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
        self.urls = {"RSS": urljoin(self.url, 'rss.php'), 'search': urljoin(self.url, 'files/')}

        self.proper_strings = ["PROPER|REPACK"]

        self.cache_rss_params = {
            "category": 12, "quality": 58, "seeded": 0, "external": 2, "sort": "added", "order": "desc"
        }

        self.cache = DemonoidCache(self)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        # https://demonoid.is/files/?category=12&quality=58&seeded=0&external=2&sort=seeders&order=desc&query=SEARCH_STRING
        search_params = {
            "category": "12",  # 12: TV
            "seeded": 0,  # 0: True
            "external": 2,  # 0: Demonoid (Only works if logged in), 1: External, 2: Both
            "order": "desc",
            "sort": self.sorting or "seeders"
        }

        for mode in search_strings:
            items = []
            logger.debug(_(f"Search Mode: {mode}"))
            if mode == "RSS":
                logger.info("Demonoid RSS search is not working through this provider yet, only string searches will work. Continuing")
                continue

            for search_string in search_strings[mode]:
                search_params["query"] = search_string
                logger.debug("Search string: {0}".format
                             (search_string))

                time.sleep(cpu_presets[settings.CPU_PRESET])

                data = self.get_url(self.urls['search'], params=search_params)
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                with BS4Parser(data, "html5lib") as html:
                    for result in html("img", alt="Download torrent"):
                        try:
                            title = result.parent['title']
                            details_url = result.parent['href']

                            if not (title and details_url):
                                if mode != "RSS":
                                    logger.debug("Discarding torrent because We could not parse the title and details")
                                continue

                            info = result.parent.parent.find_next_siblings("td")
                            size = convert_size(info[0].get_text(strip=True)) or -1
                            seeders = try_int(info[3].get_text(strip=True))
                            leechers = try_int(info[4].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                                 (title, seeders, leechers))
                                continue

                            download_url, magnet, torrent_hash = self.get_details(details_url)
                            if not all([download_url, magnet, torrent_hash]):
                                logger.info("Failed to get all required information from the details page. url:{}, magnet:{}, hash:{}".format(
                                    bool(download_url), bool(magnet), bool(torrent_hash))
                                )
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': torrent_hash}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError, Exception):
                            logger.info(traceback.format_exc())
                            continue

                            # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

                results += items

            return results

    def get_details(self, url):
        download = magnet = torrent_hash = None
        details_data = self.get_url(urljoin(self.url, url))
        if not details_data:
            logger.debug("No data returned from details page for result")
            return download, magnet, torrent_hash

        with BS4Parser(details_data, "html5lib") as html:
            magnet = html.find("img", src="/images/orange.png").parent['href'] + self._custom_trackers
            download = html.find("img", src="/images/blue.png").parent['href']
            torrent_hash = self.hash_from_magnet(magnet)

        return download, magnet, torrent_hash


class DemonoidCache(tvcache.TVCache):
    def _get_rss_data(self):
        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit('=', 1) for x in self.provider.cookies.split(';')))

        return self.get_rss_feed(self.provider.urls['RSS'], self.provider.cache_rss_params)
