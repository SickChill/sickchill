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
        super().__init__("FileList")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://filelist.io"
        self.urls = {
            "login": urljoin(self.url, "takelogin.php"),
            "search": urljoin(self.url, "browse.php"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Invalid Username/password", response) or re.search("<title> FileList :: Login </title>", response) or re.search("Login esuat!", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {"search": "", "cat": 0}

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug("Search string: {search}".format(search=search_string))

                search_params["search"] = search_string
                search_url = self.urls["search"]
                data = self.get_url(search_url, params=search_params, returns="text")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                with BS4Parser(data) as html:
                    torrent_rows = html.find_all("div", class_="torrentrow")

                    # Continue only if at least one Release is found
                    if not torrent_rows:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    # "Type", "Name", "Download", "Files", "Comments", "Added", "Size", "Snatched", "Seeders", "Leechers", "Upped by"
                    labels = []

                    columns = html.find_all("div", class_="colhead")
                    for index, column in enumerate(columns):
                        lbl = column.get_text(strip=True)
                        if lbl:
                            labels.append(str(lbl))
                        else:
                            lbl = column.find("img")
                            if lbl:
                                if lbl.has_attr("alt"):
                                    lbl = lbl["alt"]
                                    labels.append(str(lbl))
                            else:
                                if index == 3:
                                    lbl = "Download"
                                else:
                                    lbl = str(index)
                                labels.append(lbl)

                    # Skip column headers
                    for result in torrent_rows:
                        cells = result.find_all("div", class_="torrenttable")
                        if len(cells) < len(labels):
                            continue

                        try:
                            title = cells[labels.index("Name")].find("a").find("b").get_text(strip=True)
                            download_url = urljoin(self.url, cells[labels.index("Download")].find("a")["href"])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index("Seeders")].find("span").get_text(strip=True))
                            leechers = try_int(cells[labels.index("Leechers")].find("span").get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the"
                                        " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                    )
                                continue

                            torrent_size = cells[labels.index("Size")].find("span").get_text(strip=True)
                            size = convert_size(torrent_size, sep="") or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": None}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
