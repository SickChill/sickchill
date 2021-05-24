import traceback

from rtorrent import RTorrent

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super().__init__("rTorrent", host, username, password)

    def _get_auth(self):

        if self.auth is not None:
            return self.auth

        if not self.host:
            return

        self.host = self.host.rstrip("/")

        tp_kwargs = {}
        if settings.TORRENT_AUTH_TYPE and settings.TORRENT_AUTH_TYPE.lower() != "none":
            tp_kwargs["authtype"] = settings.TORRENT_AUTH_TYPE

        if not settings.TORRENT_VERIFY_CERT:
            tp_kwargs["check_ssl_cert"] = False

        if self.username and self.password:
            self.auth = RTorrent(self.host, self.username, self.password, True, tp_kwargs=tp_kwargs or None)
        else:
            self.auth = RTorrent(self.host, None, None, True, tp_kwargs=tp_kwargs or None)

        return self.auth

    def _add_torrent_uri(self, result):

        if not (self.auth and result):
            return False

        try:
            # Send torrent magnet with params to rTorrent and optionally start download
            torrent = self.auth.load_magnet(result.url, result.hash, start=not settings.TORRENT_PAUSED, params=self._get_params(result))

            if not torrent:
                return False

            return True

        except Exception as error:
            logger.warning(_("Error while sending torrent: {error}".format(error=error)))
            return False

    def _add_torrent_file(self, result):

        if not (self.auth and result):
            return False

        try:
            # Send torrent file with params to rTorrent and optionally start download
            torrent = self.auth.load_torrent(result.content, start=not settings.TORRENT_PAUSED, params=self._get_params(result))

            if not torrent:
                return False

            return True

        except Exception as error:
            logger.info(traceback.format_exc())
            logger.warning(_("Error while sending torrent: {error}".format(error=error)))
            return False

    def testAuthentication(self):
        try:
            self._get_auth()

            if self.auth is not None:
                return True, _("Success: Connected and Authenticated")
            else:
                return False, _("Error: Unable to get {self.name} Authentication, check your config!")
        except Exception as error:
            return False, _("Error: Unable to connect to {name}: {error}".format(name=self.name, error=error))

    @staticmethod
    def _get_params(result):
        params = []

        # Set label
        label = settings.TORRENT_LABEL
        if result.show.is_anime:
            label = settings.TORRENT_LABEL_ANIME
        if label:
            params.append(f"d.custom1.set={label}")

        # Set download folder
        if settings.TORRENT_PATH:
            params.append(f"d.directory.set={settings.TORRENT_PATH}")

        return params
