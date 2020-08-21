from urllib.parse import splitport

import qbittorrentapi

from sickchill import settings
from sickchill.oldbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super().__init__('qBittorrent', host, username, password)
        self.host, self.port = splitport(self.host)
        self.api = qbittorrentapi.Client(host=self.host, port=self.port or 8080, username=self.username, password=self.password)

    def _get_auth(self):
        return self.api.is_logged_in or self.api.auth_log_in()

    def testAuthentication(self):
        try:
            self._get_auth()
        except (qbittorrentapi.LoginFailed, qbittorrentapi.APIConnectionError) as error:
            return False, 'Failed to authenticate with {0}, {1}'.format(self.name, error)
        return True, 'Success: Connected and Authenticated'

    @staticmethod
    def __torrent_args(result):
        return dict(
            save_path=settings.TORRENT_DIR or None,
            category=(settings.TORRENT_LABEL, settings.TORRENT_LABEL_ANIME)[result.show.is_anime] or None,
            is_paused=settings.TORRENT_PAUSED
        )

    def _add_torrent_uri(self, result):
        return self.api.torrents_add(urls=[result.url], **self.__torrent_args(result))

    def _add_torrent_file(self, result):
        return self.api.torrents_add(torrent_files=[result.content], **self.__torrent_args(result))

    def _set_torrent_priority(self, result):
        if not self.api.app_preferences().get('queueing_enabled'):
            return True
        return (self.api.torrents_decrease_priority, self.api.torrents_increase_priority)[result.priority == 1](result.hash.lower)
