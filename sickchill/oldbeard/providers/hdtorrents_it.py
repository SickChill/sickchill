import re
from urllib.parse import quote_plus

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("HDTorrents.it")

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = 0
        self.minleech = 0
        self.freeleech = None

        self.urls = {
            "base_url": "http://hdtorrents.it",
            "login": "http://hdtorrents.it/takelogin.php",
            "search": "http://hdtorrents.it/browse.php?search=%s",
            "rss": "http://hdtorrents.it/browse.php?search=%s",
            "home": "http://hdtorrents.it/%s",
        }

        self.url = self.urls["base_url"]

        self.proper_strings = ["PROPER", "REPACK"]

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll HDTorrents every 30 minutes ma

    def _check_auth(self):

        if not self.username or not self.password:
            logger.warning("Invalid username or password. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "submit": "Accedi!"}

        response = self.get_url(self.urls["login"], post_data=login_params, timeout=30)
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Lei non e registrato in sistema.", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.debug("Search Mode: {}".format(mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    search_url = self.urls["search"] % quote_plus(search_string)
                    logger.debug("Search string: {}".format(search_string))
                else:
                    search_url = self.urls["rss"]

                if self.freeleech:
                    search_url = search_url.replace("active=1", "active=5")

                logger.debug("Search URL: {}".format(search_url))

                data = self.get_url(search_url)
                if not data or "Error" in data:
                    logger.debug("No data returned from provider")
                    continue

                if data.find("Non abbiamo trovato nulla") != -1:
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                # Search result page contains some invalid html that prevents html parser from returning all data.
                # We cut everything before the table that contains the data we are interested in thus eliminating
                # the invalid html portions
                try:
                    index = data.lower().index('<tbody id="highlighted"')
                except ValueError:
                    logger.debug("Could not find table of torrents highlighted")
                    continue

                # data = urllib.unquote(data[index:]).replace('\t', '')
                data = data[index:]

                with BS4Parser(data) as html:
                    if not html:
                        logger.debug("No html data parsed from provider")
                        continue

                    torrent_rows = []
                    torrent_table = html.find("table", class_="highlighted")
                    if torrent_table:
                        torrent_rows = torrent_table.find_all("tr")

                    if not torrent_rows:
                        logger.debug("Could not find results in returned data")
                        continue

                    # Cat., Active, Filename, Dl, Wl, Added, Size, Uploader, S, L, C
                    labels = [label.a.get_text(strip=True) if label.a else label.get_text(strip=True) for label in torrent_rows[0].find_all("td")]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result.find_all("td")[: len(labels)]
                            if len(cells) < len(labels):
                                continue

                            title = cells[labels.index(1)].a.index(0).get_text(strip=True)
                            seeders = try_int(cells[labels.index(5)].a.index(0).get_text(strip=True))
                            leechers = try_int(cells[labels.index(5)].a.index(1).get_text(strip=True))
                            torrent_size = cells[labels.index(4)].get_text()

                            size = convert_size(torrent_size) or -1
                            download_url = self.url + "/" + cells[labels.index(1)].a.index(0)["href"]
                            # title = cells[labels.index('Filename')].a.get_text(strip=True)
                            # seeders = try_int(cells[labels.index('S')].get_text(strip=True))
                            # leechers = try_int(cells[labels.index('L')].get_text(strip=True))
                            # torrent_size = cells[labels.index('Size')].get_text()

                            # size = convert_size(torrent_size) or -1
                            # download_url = self.url + '/' + cells[labels.index('Dl')].a['href']
                        except (AttributeError, TypeError, KeyError, ValueError, IndexError):
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

                        item = title, download_url, size, seeders, leechers
                        if mode != "RSS":
                            logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                        items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results
