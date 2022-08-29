import re
import traceback
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("Nebulance")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = None

        # URLs
        self.url = "https://nebulance.io/"
        self.urls = {
            "login": urljoin(self.url, "/login.php"),
            "search": urljoin(self.url, "/torrents.php"),
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "keeplogged": "on", "login": "Login"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Your username or password was incorrect.", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                search_params = {
                    "searchtext": search_string,
                    "filter_freeleech": (0, 1)[self.freeleech is True],
                    "order_by": ("seeders", "time")[mode == "RSS"],
                    "order_way": "desc",
                }

                if not search_string:
                    del search_params["searchtext"]

                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                try:
                    with BS4Parser(data) as html:
                        torrent_table = html.find("table", {"id": "torrent_table"})
                        if not torrent_table:
                            logger.debug("Data returned from {0} does not contain any torrents".format(self.name))
                            continue

                        labels = [x.get_text(strip=True) or x.a.img.get("alt") for x in torrent_table.find("tr", class_="colhead").find_all("td")]
                        torrent_rows = torrent_table("tr", class_="torrent")

                        # Continue only if one Release is found
                        if not torrent_rows:
                            logger.debug("Data returned from {0} does not contain any torrents".format(self.name))
                            continue

                        for torrent_row in torrent_rows:
                            freeleech = torrent_row.find("img", alt="Freeleech") is not None
                            if self.freeleech and not freeleech:
                                continue

                            # Normal Download Link
                            download_item = torrent_row.find("a", {"title": "Download Torrent"})

                            if not download_item:
                                # If the user has downloaded it
                                download_item = torrent_row.find("a", {"title": "Previously Grabbed Torrent File"})
                            if not download_item:
                                # If the user is seeding
                                download_item = torrent_row.find("a", {"title": "Currently Seeding Torrent"})
                            if not download_item:
                                # If the user is leeching
                                download_item = torrent_row.find("a", {"title": "Currently Leeching Torrent"})
                            if not download_item:
                                # If there are none
                                continue

                            download_url = urljoin(self.url, download_item["href"])

                            temp_anchor = torrent_row.find("a", {"data-src": True})
                            title = temp_anchor["data-src"].rsplit(".", 1)[0]
                            if not all([title, download_url]):
                                continue

                            cells = torrent_row("td")
                            seeders = try_int(cells[labels.index("∧")].text.strip())
                            leechers = try_int(cells[labels.index("∨")].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the"
                                        " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                    )
                                continue

                            size = temp_anchor["data-filesize"] or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                except Exception:
                    logger.exception("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
