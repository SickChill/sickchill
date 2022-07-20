import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Nyaa")

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.url = "https://nyaa.si"
        self.custom_url = None

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll Nyaa every 20 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if self.show and not self.show.is_anime:
            return results

        if self.custom_url:
            if validators.url(self.custom_url) != True:
                logger.warning("Invalid custom url: {0}".format(self.custom_url))
                return results

        for mode in search_strings:
            items = []
            logger.debug(_(f"Search Mode: {mode}"))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_(f"Search String: {search_string}"))

                search_params = {
                    "page": "rss",
                    "c": "1_0",  # Category: All anime
                    "s": "id",  # Sort by: 'id'=Date / 'size' / 'name' / 'seeders' / 'leechers' / 'downloads'
                    "o": "desc",  # Sort direction: asc / desc
                    "f": ("0", "2")[self.confirmed],  # Quality filter: 0 = None / 1 = No Remakes / 2 = Trusted Only
                }
                if mode != "RSS":
                    search_params["q"] = search_string

                results = []
                data = self.cache.get_rss_feed(self.custom_url or self.url, params=search_params)["entries"]
                if not data:
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                for curItem in data:
                    try:
                        title = curItem["title"]
                        download_url = curItem["link"]
                        if not all([title, download_url]):
                            continue

                        seeders = try_int(curItem["nyaa_seeders"])
                        leechers = try_int(curItem["nyaa_leechers"])
                        torrent_size = curItem["nyaa_size"]
                        info_hash = curItem["nyaa_infohash"]

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS" or 1:
                                logger.debug(f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {title} (S:{seeders} L:{leechers})")
                            continue

                        size = convert_size(torrent_size, units=["BYTES", "KIB", "MIB", "GIB", "TIB", "PIB"]) or -1
                        result = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": info_hash}
                        if mode != "RSS" or 1:
                            logger.debug(_(f"Found result: {title} with {seeders} seeders and {leechers} leechers"))

                        items.append(result)
                    except Exception:
                        continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: d.get("seeders", 0), reverse=True)
            results += items

        return results
