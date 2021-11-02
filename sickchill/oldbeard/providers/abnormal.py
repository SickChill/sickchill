import re
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("ABNormal")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://abn.lol"
        self.urls = {
            "login": urljoin(self.url, "Home/Login"),
            "search": urljoin(self.url, "Torrent"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER"]

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "Username": self.username,
            "Password": self.password,
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if not re.search("Accueil", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            "cat[]": [1, 4],  # 1 for SERIE,  4 for ANIME
            # Both ASC and DESC are available for sort direction
            "SortOrder": "desc",
            "SortOn": "Created",
        }

        # Units
        units = ["O", "Ko", "Mo", "Go", "To", "Po"]

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                search_params["search"] = re.sub(r"[()]", "", search_string)
                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find(class_="table-rows")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    # Catégorie, Release, M, DL, Taille, S, L
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]("th")]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        cells = result("td")
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index("Release")].get_text(strip=True)
                            download_url = urljoin(self.url, cells[labels.index("DL")].find("a")["href"])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index("S")].get_text(strip=True))
                            leechers = try_int(cells[labels.index("L")].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            size_index = labels.index("Size") if "Size" in labels else labels.index("Taille")
                            torrent_size = cells[size_index].get_text()
                            size = convert_size(torrent_size, units=units) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug(
                                    _(
                                        "Found result: {title} with {seeders} seeders and {leechers} leechers".format(
                                            title=title, seeders=seeders, leechers=leechers
                                        )
                                    )
                                )

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
