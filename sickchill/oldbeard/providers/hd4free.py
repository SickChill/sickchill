from urllib.parse import urljoin

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("HD4Free")

        self.url = "https://hd4free.xyz"
        self.urls = {"search": urljoin(self.url, "/searchapi.php")}

        self.freeleech = None
        self.username = None
        self.api_key = None
        self.minseed = 0
        self.minleech = 0

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll HD4Free every 10 minutes max

    def _check_auth(self):
        if self.username and self.api_key:
            return True

        logger.warning("Your authentication credentials for {0} are missing, check your config.".format(self.name))
        return False

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth:
            return results

        search_params = {"tv": "true", "username": self.username, "apikey": self.api_key}

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in {*search_strings[mode]}:
                if self.freeleech:
                    search_params["fl"] = "true"
                else:
                    search_params.pop("fl", "")

                if mode != "RSS":
                    logger.debug("Search string: " + search_string.strip())
                    search_params["search"] = search_string
                else:
                    search_params.pop("search", "")

                try:
                    jdata = self.get_url(self.urls["search"], params=search_params, returns="json")
                except ValueError:
                    logger.debug("No data returned from provider")
                    continue

                if not jdata:
                    logger.debug("No data returned from provider")
                    continue

                error = jdata.get("error")
                if error:
                    logger.debug("{}".format(error))
                    return results

                try:
                    if jdata["0"]["total_results"] == 0:
                        logger.debug("Provider has no results for this search")
                        continue
                except Exception:
                    continue

                for i in jdata:
                    try:
                        title = jdata[i]["release_name"]
                        download_url = jdata[i]["download_url"]
                        if not all([title, download_url]):
                            continue

                        seeders = jdata[i]["seeders"]
                        leechers = jdata[i]["leechers"]
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                        title, seeders, leechers
                                    )
                                )
                            continue

                        torrent_size = str(jdata[i]["size"]) + " MB"
                        size = convert_size(torrent_size) or -1
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
