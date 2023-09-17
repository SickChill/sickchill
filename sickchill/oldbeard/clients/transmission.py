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
        return self.__add_torrent(self.__make_post(result, method="uri"))

    def _add_torrent_file(self, result: "TorrentSearchResult"):
        return self.__add_torrent(self.__make_post(result, method="file"))

    def __add_torrent(self, data):
        self._request(method="post", data=json.dumps(data))
        response = self.response.json()
        success = response["result"] == "success"
        if success:
            # Torrent was successfully added, but lots of arguments given to
            # Transmission are actually not arguments supported by the
            # torrent-add command.
            # Arguments like 'seedRatioLimit' need to be set in a second pass
            # Documentation of those arguments can be found here:
            # https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md
            id = response.get("arguments", {}).get("torrent-added", {}).get("id", None)
            if id is not None:
                arguments = {"ids": id}
                for key, value in data["arguments"].items():
                    if key in (
                        "seedRatioLimit",
                        "seedRatioMode",
                        "seedIdleLimit",
                        "seedIdleMode",
                        "queuePosition",
                    ):
                        arguments[key] = value
                if len(arguments) > 1:
                    self._request(
                        method="post",
                        data=json.dumps(
                            {
                                "arguments": arguments,
                                "method": "torrent-set",
                            }
                        ),
                    )
        return success

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

        return {"arguments": arguments, "method": "torrent-add"}
