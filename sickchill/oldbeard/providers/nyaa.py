import traceback

import validators

from sickchill import logger
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider, tvcache.RSSTorrentMixin):
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

        self.size_units = ["BYTES", "KIB", "MIB", "GIB", "TIB", "PIB"]
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
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

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
                data = self.get_url(self.custom_url or self.url, params=search_params)
                if not data:
                    logger.debug("No data was returned from the provider")
                    continue

                with BS4Parser(data, language="xml") as html:
                    for item in html.find_all("item"):
                        try:
                            result = self.parse_feed_item(item, self.url, size_units=self.size_units)
                            if result:
                                if result["seeders"] < self.minseed or result["leechers"] < self.minleech:
                                    if mode != "RSS":
                                        logger.debug(
                                            f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {result['title']} (S:{result['seeders']} L:{result['leechers']})"
                                        )
                                    continue
                                items.append(result)
                        except Exception as error:
                            logger.debug(f"Error parsing results: {error}")
                            logger.debug(traceback.format_exc())
                            continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: d.get("seeders", 0), reverse=True)
            results += items

        return results
