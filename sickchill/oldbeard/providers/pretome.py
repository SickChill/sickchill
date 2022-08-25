import re
import traceback
from urllib.parse import quote

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Pretome")

        self.username = None
        self.password = None
        self.pin = None
        self.minseed = 0
        self.minleech = 0

        self.urls = {
            "base_url": "https://pretome.info",
            "login": "https://pretome.info/takelogin.php",
            "detail": "https://pretome.info/details.php?id=%s",
            "search": "https://pretome.info/browse.php?search=%s%s",
            "download": "https://pretome.info/download.php/%s/%s.torrent",
        }

        self.url = self.urls["base_url"]

        self.categories = "&st=1&cat%5B%5D=7"

        self.proper_strings = ["PROPER", "REPACK"]

        self.cache = tvcache.TVCache(self)

    def _check_auth(self):

        if not self.username or not self.password or not self.pin:
            logger.warning("Invalid username or password or pin. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "login_pin": self.pin}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Username or password incorrect", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in search_params[mode]:

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                search_url = self.urls["search"] % (quote(search_string), self.categories)

                data = self.get_url(search_url, returns="text")
                if not data:
                    continue

                try:
                    with BS4Parser(data) as html:
                        # Continue only if one Release is found
                        empty = html.find("h2", text="No .torrents fit this filter criteria")
                        if empty:
                            logger.debug("Data returned from provider does not contain any torrents")
                            continue

                        torrent_table = html.find("table", style="border: none; width: 100%;")
                        if not torrent_table:
                            logger.exception("Could not find table of torrents")
                            continue

                        torrent_rows = torrent_table("tr", class_="browse")

                        for result in torrent_rows:
                            cells = result("td")
                            size = None
                            link = cells[1].find("a", style="font-size: 1.25em; font-weight: bold;")

                            torrent_id = link["href"].replace("details.php?id=", "")

                            try:
                                if link.get("title", ""):
                                    title = link["title"]
                                else:
                                    title = link.contents[0]

                                download_url = self.urls["download"] % (torrent_id, link.contents[0])
                                seeders = int(cells[9].contents[0])
                                leechers = int(cells[10].contents[0])

                                # Need size for failed downloads handling
                                if size is None:
                                    torrent_size = cells[7].text
                                    size = convert_size(torrent_size) or -1

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                except Exception:
                    logger.exception("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
