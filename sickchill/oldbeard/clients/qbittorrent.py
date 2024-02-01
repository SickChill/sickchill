from typing import TYPE_CHECKING
from urllib.parse import urlparse

import qbittorrentapi

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient

if TYPE_CHECKING:  # pragma: no cover
    from sickchill.oldbeard.classes import TorrentSearchResult


class Client(GenericClient):
    def __init__(self, host: str = None, username: str = None, password: str = None):
        super().__init__("qBittorrent", host, username, password)
        parsed_url = urlparse(self.host or settings.TORRENT_HOST)
        self.host = parsed_url.hostname
        self.port = parsed_url.port
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

    def test_client_connection(self):
        try:
            if not self.api.is_logged_in:
                self.api.auth_log_in()
        except (qbittorrentapi.LoginFailed, qbittorrentapi.APIConnectionError) as error:
            return False, f"Failed to authenticate with {self.name}, {error}"
        return True, "Success: Connected and Authenticated"

    @staticmethod
    def __torrent_args(result: "TorrentSearchResult") -> dict:
        ratio_limit_float = max(float(result.ratio or 0), 0)

        return dict(
            save_path=settings.TORRENT_PATH or None,
            download_path=settings.TORRENT_PATH_INCOMPLETE or None,
            category=(settings.TORRENT_LABEL, settings.TORRENT_LABEL_ANIME)[result.show.is_anime] or settings.TORRENT_LABEL,
            is_paused=settings.TORRENT_PAUSED,
            ratio_limit=(None, ratio_limit_float)[ratio_limit_float > 0],
            seeding_time_limit=(None, 60 * int(settings.TORRENT_SEED_TIME))[int(settings.TORRENT_SEED_TIME) > 0],
            tags=("sickchill", "sickchill-anime")[result.show.is_anime],
        )

    def __add_trackers(self, result: "TorrentSearchResult"):
        if settings.TRACKERS_LIST and result.provider.public:
            trackers = list({x.strip() for x in settings.TRACKERS_LIST.split(",") if x.strip()})
            if trackers:
                logger.debug(f"Adding trackers to public torrent")
                return self.api.torrents_add_trackers(torrent_hash=result.hash.lower(), urls=trackers)

    def _add_torrent_uri(self, result: "TorrentSearchResult"):
        logger.debug(f"Posting as url with {self.__torrent_args(result)}")
        action = self.api.torrents_add(urls=[result.url], **self.__torrent_args(result))
        self.__add_trackers(result)
        return action

    def _add_torrent_file(self, result: "TorrentSearchResult"):
        logger.debug(f"Posting as file with {self.__torrent_args(result)}")
        action = self.api.torrents_add(torrent_files=[result.content], **self.__torrent_args(result))
        self.__add_trackers(result)
        return action

    def _set_torrent_priority(self, result: "TorrentSearchResult"):
        if not self.api.app_preferences().get("queueing_enabled"):
            return True
        return (self.api.torrents_decrease_priority, self.api.torrents_increase_priority)[result.priority == 1](result.hash.lower())
