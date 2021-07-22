import json
from urllib.parse import urlencode

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    """Main provider object"""

    def __init__(self):
        """Initialize the class"""
        super().__init__("Norbits")

        self.username = None
        self.passkey = None
        self.minseed = 0
        self.minleech = 0

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll Norbits every 15 minutes max

        self.url = "https://norbits.net"
        self.urls = {"search": self.url + "/api2.php?action=torrents", "download": self.url + "/download.php?"}

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException(("Your authentication credentials for {} are " "missing, check your config.").format(self.name))

        return True

    @staticmethod
    def _check_auth_from_data(parsed_json):
        """Check that we are authenticated."""

        if "status" in parsed_json and "message" in parsed_json and parsed_json.get("status") == 3:
            logger.warning("Invalid username or password. Check your settings")

        return True

    def search(self, search_params, age=0, ep_obj=None):
        """Do the actual searching and JSON parsing"""

        results = []

        for mode in search_params:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in search_params[mode]:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                post_data = {
                    "username": self.username,
                    "passkey": self.passkey,
                    "category": "2",  # TV Category
                    "search": search_string,
                }

                self._check_auth()
                parsed_json = self.get_url(self.urls["search"], post_data=json.dumps(post_data), returns="json")

                if not parsed_json:
                    return results

                if self._check_auth_from_data(parsed_json):
                    json_items = parsed_json.get("data", "")
                    if not json_items:
                        logger.exception("Resulting JSON from provider is not correct, " "not parsing it")

                    for item in json_items.get("torrents", []):
                        title = item.pop("name", "")
                        download_url = "{0}{1}".format(self.urls["download"], urlencode({"id": item.pop("id", ""), "passkey": self.passkey}))

                        if not all([title, download_url]):
                            continue

                        seeders = try_int(item.pop("seeders", 0))
                        leechers = try_int(item.pop("leechers", 0))

                        if seeders < self.minseed or leechers < self.minleech:
                            logger.debug(
                                "Discarding torrent because it does not meet "
                                "the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                            )
                            continue

                        info_hash = item.pop("info_hash", "")
                        size = convert_size(item.pop("size", -1), -1)

                        item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": info_hash}
                        if mode != "RSS":
                            logger.debug(
                                _(
                                    "Found result: {title} with {seeders} seeders and {leechers} leechers".format(
                                        title=title, seeders=seeders, leechers=leechers
                                    )
                                )
                            )

                        items.append(item)
            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results
