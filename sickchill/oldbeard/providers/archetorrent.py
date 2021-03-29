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
        super().__init__("ArcheTorrent")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # Freelech
        self.freeleech = False

        # URLs
        self.url = "https://www.archetorrent.com/"
        self.urls = {
            "login": urljoin(self.url, "account-login.php"),
            "search": urljoin(self.url, "torrents-search.php"),
            "download": urljoin(self.url, "download.php"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER"]

        # Cache
        self.cache = tvcache.TVCache(self, min_time=15)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "returnto": "/index.php"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        search = self.get_url(self.urls["search"])

        if not search or not re.search("torrents.php", search):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        freeleech = "2" if self.freeleech else "0"

        # Search Params
        # c59=1&c73=1&c5=1&c41=1&c60=1&c66=1&c65=1&c67=1&c62=1&c64=1&c61=1&search=Good+Behavior+S01E01&cat=0&incldead=0&freeleech=0&lang=0
        search_params = {
            "c5": "1",  # Category: Series - DVDRip
            "c41": "1",  # Category: Series - HD
            "c60": "1",  # Category: Series - Pack TV
            "c62": "1",  # Category: Series - BDRip
            "c64": "1",  # Category: Series - VOSTFR
            "c65": "1",  # Category: Series - TV 720p
            "c66": "1",  # Category: Series - TV 1080p
            "c67": "1",  # Category: Series - Pack TV HD
            "c73": "1",  # Category: Anime
            "incldead": "0",  # Include dead torrent - 0: off 1: yes 2: only dead
            "freeleech": freeleech,  # Only freeleech torrent - 0: off 1: no freeleech 2: Only freeleech
            "lang": "0",  # Langugage - 0: off 1: English 2: French ....
        }

        # Units
        units = ["B", "KB", "MB", "GB", "TB", "PB"]

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in {*search_strings[mode]}:
                logger.debug("Search String: {0} for mode {1}".format(search_strings[mode], mode))
                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                search_params["search"] = re.sub(r"[()]", "", search_string)
                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find(class_="ttable_headinner")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    # Catégorie, Release, Date, DL, Size, C, S, L
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]("th")]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        cells = result("td")
                        if len(cells) < len(labels):
                            continue

                        try:
                            id = re.search("id=([0-9]+)", cells[labels.index("Nom")].find("a")["href"]).group(1)
                            title = cells[labels.index("Nom")].get_text(strip=True)
                            download_url = urljoin(self.urls["download"], "?id={0}&name={1}".format(id, title))
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
