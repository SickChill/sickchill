import time
from base64 import b64encode
from urllib.parse import urlparse

from deluge_client import DelugeRPCClient, FailedToReconnectException

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient

from .__deluge_base import DelugeBase


class Client(GenericClient, DelugeBase):
    def __init__(self, host=None, username=None, password=None):
        super().__init__("DelugeD", host, username, password)
        self.client = None

    def setup(self):
        parsed_url = urlparse(self.host)
        if self.client and all(
            [
                self.client.host == parsed_url.hostname,
                self.client.port == parsed_url.port,
                self.client.username == self.username,
                self.client.password == self.password,
            ]
        ):
            return

        self.client = DelugeRPCClient(parsed_url.hostname, parsed_url.port or 58846, self.username, self.password)

    def _get_auth(self):
        self.setup()
        if not self.client.connected:
            try:
                for attempt in range(0, 5):
                    try:
                        self.client.connect()
                        break
                    except FailedToReconnectException:
                        time.sleep(5)
            except Exception as error:
                logger.debug(f"{self.name}: {error}")

        self.auth = self.client.connected
        return self.auth

    def _add_torrent_uri(self, result):
        remote_torrent = self.client.core.add_torrent_magnet(result.url, self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _add_torrent_file(self, result):
        if not result.content:
            result.content = {}
            return None

        remote_torrent = self.client.core.add_torrent_file(result.name + ".torrent", b64encode(result.content).decode("ascii"), self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):
        # No option for this built into the rpc, because it is a plugin
        label = settings.TORRENT_LABEL.lower()
        if result.show.is_anime:
            label = settings.TORRENT_LABEL_ANIME.lower()
        if " " in label:
            logger.exception(f"{self.name}: Invalid label. Label must not contain a space")
            return False

        if label:
            try:

                if "label" not in [x.decode().lower() for x in self.client.core.get_available_plugins()]:
                    logger.debug(f"{self.name}: label plugin not detected")
                    return False

                self.client.core.enable_plugin("Label")
                self.client.core.enable_plugin("label")

                labels = [x.decode() for x in self.client.label.get_labels()]
                if label not in labels:
                    logger.debug(f"{self.name}: {label} label does not exist in Deluge we must add it")
                    self.client.label.add(label)
                    logger.debug(f"{self.name}: [{label}] label added to deluge")

                self.client.label.set_torrent(result.hash, label)
            except Exception as error:
                logger.info(f"{self.name}: Could not add label to torrent")
                logger.debug(error)
                # logger.debug(self.client.daemon.get_method_list())
                return False

        logger.debug(f"{self.name}: [{label}] label added to torrent")
        return True

    def testAuthentication(self):
        if self._get_auth() and self.client.daemon.info():
            return True, "Success: Connected and Authenticated"
        else:
            return False, "Error: Unable to Authenticate!  Please check your config!"
