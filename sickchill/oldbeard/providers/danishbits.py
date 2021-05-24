import json

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("Danishbits")

        # Credentials
        self.username = None
        self.passkey = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

        # URLs
        self.url = "https://danishbits.org/"
        self.urls = {
            "login": self.url + "login.php",
            "search": self.url + "couchpotato.php",
        }

        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll Danishbits every 10 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            "user": self.username,
            "passkey": self.passkey,
            "search": ".",  # Dummy query for RSS search, needs the search param sent.
            "latest": "true",
        }

        # Units
        units = ["B", "KB", "MB", "GB", "TB", "PB"]

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                    search_params["latest"] = "false"
                    search_params["search"] = search_string

                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    logger.debug("No data returned from provider")
                    continue

                result = json.loads(data)
                if "results" in result:
                    for torrent in result["results"]:
                        title = torrent["release_name"]
                        download_url = torrent["download_url"]
                        seeders = torrent["seeders"]
                        leechers = torrent["leechers"]
                        if seeders < self.minseed or leechers < self.minleech:
                            logger.info(
                                "Discarded {0} because with {1}/{2} seeders/leechers does not meet the requirement of {3}/{4} seeders/leechers".format(
                                    title, seeders, leechers, self.minseed, self.minleech
                                )
                            )
                            continue

                        freeleech = torrent["freeleech"]
                        if self.freeleech and not freeleech:
                            continue

                        size = torrent["size"]
                        size = convert_size(size, units=units) or -1
                        item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                        logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))
                        items.append(item)

                if "error" in result:
                    logger.warning(result["error"])

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
