import json
from base64 import b64encode
from typing import TYPE_CHECKING

from sickchill import settings
from sickchill.oldbeard.clients.generic import GenericClient

if TYPE_CHECKING:  # pragma: no cover
    from sickchill.oldbeard.classes import TorrentSearchResult


class Client(GenericClient):
    def __init__(self, host: str = None, username: str = None, password: str = None):

        super().__init__("Transmission", host, username, password)
        self.url = "/".join((self.host.rstrip("/"), settings.TORRENT_RPCURL.strip("/"), "rpc"))

    def _get_auth(self):

        post_data = json.dumps(
            {
                "method": "session-get",
            }
        )

        try:
            self.response = self.session.post(self.url, data=post_data, timeout=120, verify=settings.TORRENT_VERIFY_CERT)
            self.auth = self.response.headers["X-Transmission-Session-Id"]
        except Exception:
            return None

        self.session.headers.update({"x-transmission-session-id": self.auth})

        # Validating Transmission authorization
        post_data = json.dumps({"arguments": {}, "method": "session-get"})

        self._request(method="post", data=post_data)

        return self.auth

    def _add_torrent_uri(self, result: "TorrentSearchResult"):
        self._request(method="post", data=self.__make_post(result, method="uri"))
        return self.response.json()["result"] == "success"

    def _add_torrent_file(self, result: "TorrentSearchResult"):
        self._request(method="post", data=self.__make_post(result, method="file"))
        return self.response.json()["result"] == "success"

    @staticmethod
    def __make_post(result, method="file"):
        arguments = {"paused": int(settings.TORRENT_PAUSED)}
        if method == "file":
            arguments.update({"metainfo": b64encode(result.content).decode("ascii")})
        else:
            arguments.update({"filename": result.url})

        if settings.TORRENT_PATH:
            arguments["download-dir"] = settings.TORRENT_PATH

        if settings.TORRENT_PATH_INCOMPLETE:
            arguments["incomplete-dir"] = settings.TORRENT_PATH_INCOMPLETE
            arguments["incomplete-enabled"] = 1

        ratio = None
        if result.ratio:
            ratio = result.ratio

        mode = 0
        if ratio:
            if float(ratio) == -1:
                ratio = 0
                mode = 2
            elif float(ratio) >= 0:
                ratio = float(ratio)
                mode = 1  # Stop seeding at seedRatioLimit

        arguments.update({"seedRatioLimit": ratio, "seedRatioMode": mode})

        if settings.TORRENT_SEED_TIME and settings.TORRENT_SEED_TIME != -1:
            time = int(60 * float(settings.TORRENT_SEED_TIME))
            arguments.update({"seedIdleLimit": time, "seedIdleMode": 1})

        if result.priority == -1:
            arguments["priority-low"] = []
        elif result.priority == 1:
            # set high priority for all files in torrent
            arguments["priority-high"] = []
            # move torrent to the top if the queue
            arguments["queuePosition"] = 0
            if settings.TORRENT_HIGH_BANDWIDTH:
                arguments["bandwidthPriority"] = 1
        else:
            arguments["priority-normal"] = []

        return json.dumps({"arguments": arguments, "method": "torrent-add"})
