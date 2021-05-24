import re
import traceback

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("GimmePeers")

        self.urls = {
            "base_url": "https://www.gimmepeers.com",
            "login": "https://www.gimmepeers.com/takelogin.php",
            "detail": "https://www.gimmepeers.com/details.php?id=%s",
            "search": "https://www.gimmepeers.com/browse.php",
            "download": "https://gimmepeers.com/%s",
        }

        self.url = self.urls["base_url"]

        self.username = None
        self.password = None
        self.minseed = 0
        self.minleech = 0

        self.cache = tvcache.TVCache(self)

        self.search_params = {
            # c20=1&c21=1&c25=1&c24=1&c23=1&c22=1&c1=1
            "c20": 1,
            "c21": 1,
            "c25": 1,
            "c24": 1,
            "c23": 1,
            "c22": 1,
            "c1": 1,
        }

    def _check_auth(self):
        if not self.username or not self.password:
            logger.warning("Invalid username or password. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "ssl": "yes"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Username or password incorrect!", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                self.search_params["search"] = search_string

                data = self.get_url(self.urls["search"], params=self.search_params, returns="text")
                if not data:
                    continue

                # Checks if cookie has timed-out causing search to redirect to login page.
                # If text matches on loginpage we login and generate a new cookie and load the search data again.
                if re.search("Still need help logging in?", data):
                    logger.debug("Login has timed out. Need to generate new cookie for GimmePeers and search again.")
                    self.session.cookies.clear()
                    self.login()

                    data = self.get_url(self.urls["search"], params=self.search_params, returns="text")
                    if not data:
                        continue

                try:
                    with BS4Parser(data, "html.parser") as html:
                        torrent_table = html.find("table", class_="browsetable")
                        torrent_rows = torrent_table("tr") if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for result in torrent_rows[1:]:
                            cells = result("td")

                            link = cells[1].find("a")
                            download_url = self.urls["download"] % cells[2].find("a")["href"]

                            try:
                                title = link.getText()
                                seeders = int(cells[10].getText().replace(",", ""))
                                leechers = int(cells[11].getText().replace(",", ""))
                                torrent_size = cells[8].getText()
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

                            if seeders >= 32768 or leechers >= 32768:
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                except Exception:
                    logger.warning("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
