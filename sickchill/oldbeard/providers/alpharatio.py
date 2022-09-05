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
        super().__init__("AlphaRatio")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "http://alpharatio.cc"
        self.urls = {
            "login": urljoin(self.url, "login.php"),
            "search": urljoin(self.url, "torrents.php"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "username": self.username,
            "password": self.password,
            "login": "submit",
            "remember_me": "on",
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Invalid Username/password", response) or re.search("<title>Login :: AlphaRatio.cc</title>", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            "searchstr": "",
            "filter_cat[1]": 1,
            "filter_cat[2]": 1,
            "filter_cat[3]": 1,
            "filter_cat[4]": 1,
            "filter_cat[5]": 1,
            "filter_cat[6]": 1,
            "filter_cat[7]": 1,
        }

        def process_column_header(td):
            result = ""
            if td.a and td.a.img:
                result = td.a.img.get("title", td.a.get_text(strip=True))
            if not result:
                result = td.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                search_params["searchstr"] = search_string
                search_url = self.urls["search"]
                data = self.get_url(search_url, params=search_params, returns="text")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                with BS4Parser(data) as html:
                    torrent_table = html.find("table", id="torrent_table")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    # "", "", "Name /Year", "Files", "Time", "Size", "Snatches", "Seeders", "Leechers"
                    labels = [process_column_header(label) for label in torrent_rows[0]("td")]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        cells = result("td")
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index("Name /Year")].find("a", dir="ltr").get_text(strip=True)
                            download_url = urljoin(self.url, cells[labels.index("Name /Year")].find("a", title="Download")["href"])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index("Seeders")].get_text(strip=True))
                            leechers = try_int(cells[labels.index("Leechers")].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the"
                                        " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                    )
                                continue

                            torrent_size = cells[labels.index("Size")].get_text(strip=True)
                            size = convert_size(torrent_size) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
