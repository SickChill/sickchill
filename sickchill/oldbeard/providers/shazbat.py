from urllib.parse import urljoin

from sickchill import logger
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Shazbat.tv")

        self.supports_backlog = False

        self.passkey = None
        self.options = None

        self.cache = ShazbatCache(self, min_time=20)

        self.url = "http://www.shazbat.tv"
        self.urls = {
            "login": urljoin(self.url, "login"),
            "rss_recent": urljoin(self.url, "rss/recent"),
            # 'rss_queue': urljoin(self.url, 'rss/download_queue'),
            # 'rss_followed': urljoin(self.url, 'rss/followed')
        }

    def _check_auth(self):
        if not self.passkey:
            raise AuthException("Your authentication credentials are missing, check your config.")

        return True

    def _check_auth_from_data(self, data):
        if not self.passkey:
            self._check_auth()
        elif data.get("bozo") == 1 and not (data["entries"] and data["feed"]):
            logger.warning("Invalid username or password. Check your settings")

        return True


class ShazbatCache(tvcache.TVCache):
    def _get_rss_data(self):
        params = {"passkey": self.provider.passkey, "fname": "true", "limit": 100, "duration": "2 hours"}

        return self.get_rss_feed(self.provider.urls["rss_recent"], params=params)

    def _check_auth(self, data):
        return self.provider._check_auth_from_data(data)
