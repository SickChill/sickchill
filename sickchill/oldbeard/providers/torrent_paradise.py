# https://github.com/urbanguacamole/torrent-paradise

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("torrent-paradise")
        self.minseed = 0
        self.minleech = 0
        self.supports_movies = True
        self.ability_status = self.PROVIDER_BACKLOG

        self.url = "https://torrent-paradise.ml"
        self.urls = {"search": "https://torrent-paradise.ml/api/search"}

        self.cache = tvcache.TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if "RSS" in search_strings:
            del search_strings["RSS"]

        for mode in search_strings:
            items = []

            search_string = " OR ".join(search_strings[mode])
            logger.debug(_("Search String: {search_string}").format(search_string=search_string))

            data = self.get_url(self.urls["search"], params={"q": search_string}, returns="json")

            if not isinstance(data, list):
                logger.debug("No data returned from provider")
                continue

            if not data:
                logger.debug("Data returned from provider does not contain any torrents")
                continue

            logger.info(f"Number of torrents found on {self.name} = {len(data)}")

            for item in data:
                try:
                    title = item.pop("text")
                    info_hash = item.pop("id")
                    if not all([title, info_hash]):
                        continue

                    seeders = item.pop("s")
                    leechers = item.pop("l")

                    if seeders < self.minseed or leechers < self.minleech:
                        logger.debug(f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {title} (S:{seeders} L:{leechers})")
                        continue

                    size = item.pop("len")
                    logger.debug(f"Found result: {title} with {seeders} seeders and {leechers} leechers with a file size {size}")

                    items.append(
                        {
                            "title": title,
                            "size": size,
                            "seeders": seeders,
                            "leechers": leechers,
                            "hash": info_hash,
                            "link": f"magnet:?xt=urn:btih:{info_hash}&dn={title}{self._custom_trackers}",
                        }
                    )
                except Exception as error:
                    raise error

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items
        return results
