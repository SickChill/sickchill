import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("TorrentProject")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://torrentproject.to/"

        self.custom_url = None

        self.ability_status = self.PROVIDER_BACKLOG
        # Proper Strings

        # Cache
        self.cache = tvcache.TVCache(self, search_params={"RSS": ["0day"]})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        search_params = {"out": "json", "filter": 2101, "showmagnets": "on", "num": 50}

        for mode in search_strings:  # Mode = RSS, Season, Episode
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in {*search_strings[mode]}:

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                search_params["s"] = search_string

                if self.custom_url:
                    if validators.url(self.custom_url) != True:
                        logger.warning("Invalid custom url set, please check your settings")
                        return results
                    search_url = self.custom_url
                else:
                    search_url = self.url

                torrents = self.get_url(search_url, params=search_params, returns="json")
                if not (torrents and "total_found" in torrents and int(torrents["total_found"]) > 0):
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                del torrents["total_found"]

                results = []
                for i in torrents:
                    title = torrents[i]["title"]
                    seeders = try_int(torrents[i]["seeds"], 1)
                    leechers = try_int(torrents[i]["leechs"], 0)
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != "RSS":
                            logger.debug("Torrent doesn't meet minimum seeds & leechers not selecting : {0}".format(title))
                        continue

                    t_hash = torrents[i]["torrent_hash"]
                    torrent_size = torrents[i]["torrent_size"]
                    if not all([t_hash, torrent_size]):
                        continue
                    download_url = torrents[i]["magnet"] + self._custom_trackers
                    size = convert_size(torrent_size) or -1

                    if not all([title, download_url]):
                        continue

                    item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": t_hash}

                    if mode != "RSS":
                        logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
