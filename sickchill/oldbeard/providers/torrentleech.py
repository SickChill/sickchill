import re
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("TorrentLeech")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://www.torrentleech.org"
        self.urls = {
            "login": urljoin(self.url, "user/account/login/"),
            "search": urljoin(self.url, "torrents/browse/list/"),
            "download": urljoin(self.url, "download/"),
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
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Invalid Username/password", response) or re.search("<title>Login :: TorrentLeech.org</title>", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # TV, Episodes, BoxSets, Episodes HD, Animation, Anime, Cartoons
        # 2,26,27,32,7,34,35

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                    categories = ["2", "7", "35"]
                    categories += ["26", "32"] if mode == "Episode" else ["27"]
                    if self.show and self.show.is_anime:
                        categories += ["34"]
                else:
                    categories = ["2", "26", "27", "32", "7", "34", "35"]

                # Craft the query URL
                categories_url = "categories/{categories}/".format(categories=",".join(categories))
                query_url = "query/{query_string}".format(query_string=search_string)
                params_url = urljoin(categories_url, query_url)
                search_url = urljoin(self.urls["search"], params_url)

                data = self.get_url(search_url, returns="json")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                # TODO: Handle more than 35 torrents in return. (Max 35 per call)
                torrent_list = data["torrentList"]

                if len(torrent_list) < 1:
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                for torrent in torrent_list:
                    try:
                        title = torrent["name"]
                        download_url = urljoin(self.urls["download"], "{id}/{filename}".format(id=torrent["fid"], filename=torrent["filename"]))

                        seeders = torrent["seeders"]
                        leechers = torrent["leechers"]

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.debug(
                                    "Discarding torrent because it doesn't meet the"
                                    " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                )
                                continue

                        size = torrent["size"]

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
