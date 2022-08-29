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

        super().__init__("HoundDawgs")

        self.username = None
        self.password = None
        self.minseed = 0
        self.minleech = 0
        self.freeleech = None
        self.ranked = None

        self.urls = {"base_url": "https://hounddawgs.org/", "search": "https://hounddawgs.org/torrents.php", "login": "https://hounddawgs.org/login.php"}

        self.url = self.urls["base_url"]

        self.search_params = {
            "filter_cat[85]": 1,
            "filter_cat[58]": 1,
            "filter_cat[57]": 1,
            "filter_cat[74]": 1,
            "filter_cat[92]": 1,
            "filter_cat[93]": 1,
            "order_by": "s3",
            "order_way": "desc",
            "type": "",
            "userid": "",
            "searchstr": "",
            "searchimdb": "",
            "searchtags": "",
        }

        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {"username": self.username, "password": self.password, "keeplogged": "on", "login": "Login"}

        self.get_url(self.urls["base_url"], returns="text")
        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if (
            re.search("Dit brugernavn eller kodeord er forkert.", response)
            or re.search("<title>Login :: HoundDawgs</title>", response)
            or re.search("Dine cookies er ikke aktiveret.", response)
        ):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                self.search_params["searchstr"] = search_string

                data = self.get_url(self.urls["search"], params=self.search_params, returns="text")
                if not data:
                    logger.debug("URL did not return data")
                    continue

                strTableStart = '<table class="torrent_table'
                startTableIndex = data.find(strTableStart)
                trimmedData = data[startTableIndex:]
                if not trimmedData:
                    continue

                try:
                    with BS4Parser(trimmedData, "html5lib") as html:
                        result_table = html.find("table", {"id": "torrent_table"})

                        if not result_table:
                            logger.debug("Data returned from provider does not contain any torrents")
                            continue

                        result_tbody = result_table.find("tbody")
                        entries = result_tbody.contents
                        del entries[1::2]

                        for result in entries[1:]:

                            torrent = result("td")
                            if len(torrent) <= 1:
                                break

                            allAs = (torrent[1])("a")

                            try:
                                notinternal = result.find_next("img", src="/static//common/user_upload.png")
                                if self.ranked and notinternal:
                                    logger.debug("Found a user uploaded release, Ignoring it..")
                                    continue
                                freeleech = result.find_next("img", src="/static//common/browse/freeleech.png")
                                if self.freeleech and not freeleech:
                                    continue
                                title = allAs[2].string
                                download_url = self.urls["base_url"] + allAs[0].attrs["href"]
                                torrent_size = result.find_next("td", class_="nobr").find_next_sibling("td").string
                                if torrent_size:
                                    size = convert_size(torrent_size) or -1
                                seeders = try_int((result("td")[6]).text.replace(",", ""))
                                leechers = try_int((result("td")[7]).text.replace(",", ""))

                            except (AttributeError, TypeError):
                                continue

                            if not title or not download_url:
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
