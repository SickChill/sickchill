import re
import traceback
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
        super().__init__("Speedcd")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = False

        self.enable_cookies = True

        # URLs
        self.url = "https://speed.cd"
        self.urls = {
            "login": urljoin(self.url, "takeElogin.php"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if self.cookies:
            logger.debug(self.add_cookies_from_ui()[1])

        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "username": self.username,
            "password": self.password,
        }

        # Yay lets add another request to the process since they are unreasonable.
        response = self.get_url(self.url, returns="text")
        with BS4Parser(response, "html5lib") as html:
            form = html.find("form", id="loginform")
            if form:
                self.urls["login"] = urljoin(self.url, form["action"])

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Incorrect username or Password. Please try again.", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # http://speed.cd/browse/49/50/52/41/55/2/30/freeleech/deep/q/arrow
        # Search Params
        search_params = [
            "browse",
            "41",  # TV/Packs
            "2",  # Episodes
            "49",  # TV/HD
            "50",  # TV/Sports
            "52",  # TV/B-Ray
            "55",  # TV/Kids
            "30",  # Anime
        ]
        if self.freeleech:
            search_params.append("freeleech")
        search_params.append("deep")

        def process_column_header(td):
            result = ""
            img = td.find("img")
            if img:
                result = img.get("alt")
                if not result:
                    result = img.get("title")

            if not result:
                anchor = td.find("a")
                if anchor:
                    result = anchor.get_text(strip=True)

            if not result:
                result = td.get_text(strip=True)
            return result

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            for search_string in {*search_strings[mode]}:
                current_params = search_params
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))
                    current_params += ["q", re.sub(r"[^\w\s]", "", search_string)]

                data = self.get_url(urljoin(self.url, "/".join(current_params)), returns="text")
                if not data:
                    continue

                with BS4Parser(data) as html:
                    torrent_table = html.find("div", class_="boxContent")
                    torrent_table = torrent_table.find("table") if torrent_table else []
                    # noinspection PyCallingNonCallable
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0]("th")]
                    row_labels = [process_column_header(label) for label in torrent_rows[1]("td")]

                    def label_index(name):
                        if name in labels:
                            return labels.index(name)
                        return row_labels.index(name)

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result("td")
                            title = cells[label_index("Title")].find("a").get_text()
                            download_url = urljoin(self.url, cells[label_index("Download")].a["href"])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[label_index("Seeders") - 1].get_text(strip=True))
                            leechers = try_int(cells[label_index("Leechers") - 1].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            torrent_size = cells[label_index("Size") - 1].get_text()
                            size = convert_size(torrent_size) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception as error:
                            logger.debug(f"Speed.cd: {error}")
                            logger.debug(traceback.format_exc())
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
