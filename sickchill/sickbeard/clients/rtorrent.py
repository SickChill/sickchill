from rtorrent import RTorrent

from sickchill import settings, logger
from sickchill.sickbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('rTorrent', host, username, password)

    def _get_auth(self):

        if self.auth is not None:
            return self.auth

        if not self.host:
            return

        tp_kwargs = {}
        if settings.TORRENT_AUTH_TYPE != 'none':
            tp_kwargs['authtype'] = settings.TORRENT_AUTH_TYPE

        if not settings.TORRENT_VERIFY_CERT:
            tp_kwargs['check_ssl_cert'] = False

        if self.username and self.password:
            self.auth = RTorrent(self.host, self.username, self.password, True, tp_kwargs=tp_kwargs)
        else:
            self.auth = RTorrent(self.host, None, None, True, tp_kwargs=tp_kwargs)

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
            logger.warning('Error while sending torrent: {error}'.format
                           (error=str(error)))
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
            logger.warning('Error while sending torrent: {error}'.format
                           (error=str(error)))
            return False

    def testAuthentication(self):
        try:
            self._get_auth()

            if self.auth is not None:
                return True, 'Success: Connected and Authenticated'
            else:
                return False, 'Error: Unable to get {name} Authentication, check your config!'.format(name=self.name)
        except Exception:
            return False, 'Error: Unable to connect to {name}'.format(name=self.name)

    @staticmethod
    def _get_params(result):
        params = []

        # Set label
        label = settings.TORRENT_LABEL
        if result.show.is_anime:
            label = settings.TORRENT_LABEL_ANIME
        if label:
            params.append('d.custom1.set={0}'.format(label))

        # Set download folder
        if settings.TORRENT_PATH:
            params.append('d.directory.set={0}'.format(settings.TORRENT_PATH))

        return params
