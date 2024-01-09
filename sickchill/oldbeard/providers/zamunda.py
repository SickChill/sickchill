import re
from urllib.parse import quote_plus

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):
        super().__init__("Zamunda")

        self.username = None
        self.password = None
        self.minseed = 0
        self.minleech = 0

        self.custom_url = None

        self.urls = {
            "base_url": "https://zamunda.net",
            "login": "https://zamunda.net/takelogin.php",
            "search": "https://zamunda.net/bananas?c7=1&c33=1&c55=1&search=%s",
            "change_language": "https://zamunda.net/langchange.php?lang=en",
        }

        self.url = self.urls["base_url"]
        self.categories = "&c7=1&c33=1&c55=1"

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll Zamunda every 30 minutes max

    def _check_auth(self):
        if not self.username or not self.password:
            raise AuthException("Invalid username or password. Check your settings")

        return True

    def login(self):
        if not self.check_and_update_urls():
            return False

        cookie_dict = dict_from_cookiejar(self.session.cookies)
        if cookie_dict.get("uid") and cookie_dict.get("pass"):
            return True

        change_language_response = self.get_url(self.urls["change_language"], returns="text")
        if not change_language_response:
            logger.warning(_("Unable to connect to provider"))
            return False

        login_params = {"username": self.username, "password": self.password}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning(_("Unable to connect to provider"))
            return False

        if re.search("Login failed!", response):
            logger.warning(_("Invalid username or password. Check your settings"))
            return False

        return True

    def search(self, search_strings, ep_obj=None):
        results = []

        if not self.login():
            return results

        if "RSS" in search_strings:
            del search_strings["RSS"]

        for mode in search_strings:
            items = []

            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                search_url = self.urls["search"] % quote_plus(search_string) + self.categories
                logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                data = self.get_url(search_url, returns="text")
                if not data or "Flood protection is activated. Please, wait few seconds to continue." in data:
                    logger.debug(_("Flood protection is activated"))
                    continue

                if data.find("Sorry, nothing found") != -1:
                    logger.debug(_("Data returned from provider does not contain any torrents"))
                    continue

                # Search result page contains some invalid html that prevents html parser from returning all data.
                # We cut everything before the table that contains the data we are interested in thus eliminating
                # the invalid html portions
                try:
                    index = data.lower().index('<table align="center" id="zbtable"')
                except ValueError:
                    logger.debug(_("Could not find table of torrents zbtable"))
                    continue

                data = data[index:]

                with BS4Parser(data) as html:
                    if not html:
                        logger.debug(_("No html data parsed from provider"))
                        continue

                    torrent_rows = []
                    torrent_table = html.find("table", class_="test bottom responsivetable responsetop td_clear roundrss")
                    if torrent_table:
                        torrent_rows = torrent_table("tr")

                    if not torrent_rows:
                        logger.debug(_("Could not find results in returned data"))
                        continue

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result.find_all("td")

                            imdrating = cells[1].find("div", class_="imdrating")
                            download_url = imdrating.select_one("a")["href"]

                            dString = str(download_url)
                            start = dString.rindex("/") + 1
                            end = dString.index(".torrent")
                            title = dString[start:end]

                            torrent_size = cells[5].get_text(strip=True)
                            seeders = try_int(cells[7].get_text(strip=True))
                            leechers = try_int(cells[8].get_text(strip=True))

                            size = convert_size(torrent_size) or -1
                        except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.debug(
                                    _("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})").format(
                                        title, seeders, leechers
                                    )
                                )
                            continue

                        item = {"title": title, "link": self.url + download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}

                        items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
