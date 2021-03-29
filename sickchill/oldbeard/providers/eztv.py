from urllib.parse import urljoin

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        # Provider Init
        super().__init__("EZTV")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0

        # URLs
        self.url = "https://eztv.re"
        self.api = urljoin(self.url, "api/get-torrents")

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        search_params = {"imdb_id": None, "page": 1, "limit": 100}

        # Just doing the first page of results, because there is no search filter
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            if mode != "RSS":
                if not (self.show and self.show.imdb_id):
                    continue

                search_params["imdb_id"] = self.show.imdb_id.strip("tt")
                logger.debug("Search string: {}".format(self.show.imdb_id))
            else:
                search_params.pop("imdb_id")

            data = self.get_url(self.api, params=search_params, returns="json")

            if not (data and isinstance(data, dict) and "torrents" in data):
                logger.debug("URL did not return data")
                continue

            for result in data["torrents"]:
                try:
                    title = result["title"][0:-5].replace(" ", ".")
                    info_hash = result["hash"]
                    if not all([title, info_hash]):
                        continue

                    link = result[("magnet_url", "torrent_url")[settings.TORRENT_METHOD == "blackhole"]]

                    seeders = result["seeds"]
                    leechers = result["peers"]

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != "RSS":
                            logger.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                            )
                        continue

                    torrent_size = try_int(result["size_bytes"])

                    item = {"title": title, "link": link, "size": torrent_size, "seeders": seeders, "leechers": leechers, "hash": info_hash}
                    if mode != "RSS":
                        logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                    items.append(item)
                except Exception:
                    continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
