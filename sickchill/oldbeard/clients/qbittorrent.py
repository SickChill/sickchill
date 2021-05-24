from typing import TYPE_CHECKING
from urllib.parse import splitport

import qbittorrentapi

from sickchill import settings
from sickchill.oldbeard.clients.generic import GenericClient

if TYPE_CHECKING:  # pragma: no cover
    from sickchill.oldbeard.classes import TorrentSearchResult


class Client(GenericClient):
    def __init__(self, host: str = None, username: str = None, password: str = None):
        super().__init__("qBittorrent", host, username, password)
        self.host, self.port = splitport(self.host or settings.TORRENT_HOST)
        self.api = qbittorrentapi.Client(
            host=self.host,
            port=self.port or None,
            username=self.username or settings.TORRENT_USERNAME,
            password=self.password or settings.TORRENT_PASSWORD,
            VERIFY_WEBUI_CERTIFICATE=settings.TORRENT_VERIFY_CERT,
        )

    def _get_auth(self):
        try:
            if not self.api.is_logged_in:
                self.api.auth_log_in()
        except (qbittorrentapi.LoginFailed, qbittorrentapi.APIConnectionError):
            return False
        return True

    def testAuthentication(self):
        try:
            if not self.api.is_logged_in:
                self.api.auth_log_in()
        except (qbittorrentapi.LoginFailed, qbittorrentapi.APIConnectionError) as error:
            return False, f"Failed to authenticate with {self.name}, {error}"
        return True, "Success: Connected and Authenticated"

    @staticmethod
    def __torrent_args(result: "TorrentSearchResult"):
        return dict(
            save_path=settings.TORRENT_DIR or None,
            category=(settings.TORRENT_LABEL, settings.TORRENT_LABEL_ANIME)[result.show.is_anime] or settings.TORRENT_LABEL,
            is_paused=settings.TORRENT_PAUSED,
        )

    def _add_torrent_uri(self, result: "TorrentSearchResult"):
        return self.api.torrents_add(urls=[result.url], **self.__torrent_args(result))

    def _add_torrent_file(self, result: "TorrentSearchResult"):
        return self.api.torrents_add(torrent_files=[result.content], **self.__torrent_args(result))

    def _set_torrent_priority(self, result: "TorrentSearchResult"):
        if not self.api.app_preferences().get("queueing_enabled"):
            return True
        return (self.api.torrents_decrease_priority, self.api.torrents_increase_priority)[result.priority == 1](result.hash.lower)
