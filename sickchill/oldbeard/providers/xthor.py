import time

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("XThor")

        self.url = "https://xthor.tk"
        self.urls = {"search": "https://api.xthor.tk"}

        self.freeleech = None
        self.api_key = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll XThor every 10 minutes max

    def _check_auth(self):
        if self.api_key:
            return True

        logger.warning("Your authentication credentials for {0} are missing, check your config.".format(self.name))
        return False

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth:
            return results

        search_params = {"passkey": self.api_key}
        if self.freeleech:
            search_params["freeleech"] = 1

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug("Search string: " + search_string.strip())
                    search_params["search"] = search_string
                else:
                    search_params.pop("search", "")

                jdata = self.get_url(self.urls["search"], params=search_params, returns="json")
                time.sleep(3)
                if not jdata:
                    logger.debug(_("No data returned from provider"))
                    continue

                error_code = jdata.pop("error", {})
                if error_code.get("code"):
                    if error_code.get("code") != 2:
                        logger.warning("{0}".format(error_code.get("descr", "Error code 2 - no description available")))
                        return results
                    continue

                account_ok = jdata.pop("user", {}).get("can_leech")
                if not account_ok:
                    logger.warning("Sorry, your account is not allowed to download, check your ratio")
                    return results

                torrents = jdata.pop("torrents", None)
                if not torrents:
                    logger.debug("Provider has no results for this search")
                    continue

                for torrent in torrents:
                    try:
                        title = torrent.get("name")
                        download_url = torrent.get("download_link")
                        if not (title and download_url):
                            continue

                        seeders = torrent.get("seeders")
                        leechers = torrent.get("leechers")
                        if not seeders and mode != "RSS":
                            logger.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                            )
                            continue

                        size = torrent.get("size") or -1
                        item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}

                        if mode != "RSS":
                            logger.debug(
                                _(
                                    "Found result: {title} with {seeders} seeders and {leechers} leechers".format(
                                        title=title, seeders=seeders, leechers=leechers
                                    )
                                )
                            )

                        items.append(item)
                    except Exception:
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
