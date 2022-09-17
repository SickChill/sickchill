import json
from base64 import b64encode
from urllib.parse import urljoin

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient

from .__deluge_base import DelugeBase


class Client(GenericClient, DelugeBase):
    def __init__(self, host=None, username=None, password=None):
        super().__init__("Deluge", host, username, password)

        self.url = urljoin(self.host, "json")
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_auth(self):

        post_data = json.dumps({"method": "auth.login", "params": [self.password], "id": 1})

        try:
            self.response = self.session.post(self.url, data=post_data, verify=settings.TORRENT_VERIFY_CERT)
        except Exception as error:
            logger.info(error)
            return None

        self.auth = self.response.json()["result"]

        post_data = json.dumps({"method": "web.connected", "params": [], "id": 10})

        try:
            self.response = self.session.post(self.url, data=post_data, verify=settings.TORRENT_VERIFY_CERT)
        except Exception:
            return None

        connected = self.response.json()["result"]

        if not connected:
            post_data = json.dumps({"method": "web.get_hosts", "params": [], "id": 11})
            try:
                self.response = self.session.post(self.url, data=post_data, verify=settings.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            hosts = self.response.json()["result"]
            if not hosts:
                logger.exception(self.name + ": WebUI does not contain daemons")
                return None

            post_data = json.dumps({"method": "web.connect", "params": [hosts[0][0]], "id": 11})

            try:
                self.response = self.session.post(self.url, data=post_data, verify=settings.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            post_data = json.dumps({"method": "web.connected", "params": [], "id": 10})

            try:
                self.response = self.session.post(self.url, data=post_data, verify=settings.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            connected = self.response.json()["result"]
            if not connected:
                logger.exception(self.name + ": WebUI could not connect to daemon")
                return None

        return self.auth

    def _add_torrent_uri(self, result):
        post_data = json.dumps({"method": "core.add_torrent_magnet", "params": [result.url, self.make_options(result)], "id": 2})

        self._request(method="post", data=post_data)

        result.hash = self.response.json()["result"]

        return self.response.json()["result"]

    def _add_torrent_file(self, result):
        post_data = json.dumps(
            {
                "method": "core.add_torrent_file",
                "params": [result.name + ".torrent", b64encode(result.content).decode("ascii"), self.make_options(result)],
                "id": 2,
            }
        )

        self._request(method="post", data=post_data)

        result.hash = self.response.json()["result"]

        return self.response.json()["result"]

    def _set_torrent_label(self, result):

        label = settings.TORRENT_LABEL.lower()
        if result.show.is_anime:
            label = settings.TORRENT_LABEL_ANIME.lower()
        if " " in label:
            logger.exception(self.name + ": Invalid label. Label must not contain a space")
            return False

        if label:
            # check if label already exists and create it if not
            post_data = json.dumps({"method": "label.get_labels", "params": [], "id": 3})

            self._request(method="post", data=post_data)
            labels = self.response.json()["result"]

            if labels is not None:
                if label not in labels:
                    logger.debug(self.name + ": " + label + " label does not exist in Deluge we must add it")
                    post_data = json.dumps({"method": "label.add", "params": [label], "id": 4})

                    self._request(method="post", data=post_data)
                    logger.debug(self.name + ": " + label + " label added to Deluge")

                # add label to torrent
                post_data = json.dumps({"method": "label.set_torrent", "params": [result.hash, label], "id": 5})

                self._request(method="post", data=post_data)
                logger.debug(self.name + ": " + label + " label added to torrent")
            else:
                logger.debug(self.name + ": " + "label plugin not detected")
                return False

        return not self.response.json()["error"]
