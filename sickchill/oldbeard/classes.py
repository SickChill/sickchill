import datetime
import re
import sys
from typing import List, TYPE_CHECKING, Union

import sickchill
from sickchill.helper.common import dateTimeFormat

from .common import Quality

if TYPE_CHECKING:
    from ..providers.GenericProvider import GenericProvider
    from ..tv import TVEpisode, TVShow


class SearchResult(object):
    """
    Represents a search result from an indexer.
    """

    def __init__(self, episodes):
        self.provider: Union["GenericProvider", None] = None

        # release show object
        self.show: Union["TVShow", None] = None

        # URL to the NZB/torrent file
        self.url: str = ""

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # list of TVEpisode objects that this result is associated with
        self.episodes: List["TVEpisode"] = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # release name
        self.name: str = ""

        # size of the release (-1 = n/a)
        self.size: int = -1

        # release group
        self.release_group: str = ""

        # version
        self.version: int = -1

        # hash
        self.hash: str = ""

        # content
        self.content = None

        self.result_type: str = ""

        self.priority: int = 0

        self.__checked_url: bool = False

    def from_json(self, result_dict):
        self.name = result_dict.get("name")
        self.url = result_dict.get("url")
        self.size = result_dict.get("size")
        self.version = result_dict.get("version")
        self.release_group = result_dict.get("release_group")
        self.quality = int(result_dict.get("quality"))
        self.provider = sickchill.oldbeard.providers.getProviderClass(result_dict.get("provider"))

    @classmethod
    def make_result(cls, result_dict):
        show = sickchill.show.Show.Show.validate_indexer_id(result_dict.get("indexerid"))
        if not show[1]:
            return show[0]

        show = show[1]
        episode_objects = [show.getEpisode(result_dict.get("season"), ep) for ep in result_dict.get("episodes").split("|") if ep]
        result = cls(episode_objects)
        result.from_json(result_dict)
        result.show = show

        return result

    def __check_url(self):
        if not self.__checked_url and self.url and "jackett_apikey" in self.url:
            response = self.provider.get_url(self.url, allow_redirects=False, returns="response")
            if response.next and response.next.url and response.next.url.startswith("magnet:") and re.search(r"urn:btih:(\w{32,40})", self.url):
                self.url = response.next.url
        self.__checked_url = True

    @property
    def __check_torznab(self) -> bool:
        torznab: bool = hasattr(self.provider, "torznab") and bool(self.provider.torznab)
        torznab |= bool(self.url) and "jackett" in self.url
        torznab |= self.url.startswith("magnet:") and bool(re.search(r"urn:btih:(\w{32,40})", self.url))
        return torznab

    @property
    def is_torrent(self) -> bool:
        self.__check_url()
        if self.__check_torznab:
            return True
        return self.result_type == "torrent"

    @property
    def is_nzb(self) -> bool:
        if self.is_torrent:
            return False
        return self.result_type == "nzb"

    @property
    def is_nzbdata(self) -> bool:
        if self.is_torrent:
            return False
        return self.result_type == "nzbdata"

    def __str__(self) -> str:
        if self.provider is None:
            return "Invalid provider, unable to print self"

        my_string = f"{self.provider.name} @ {self.url}\n"
        my_string += "Extra Info:\n"
        for extra in self.extraInfo:
            my_string += f" {extra}\n"

        my_string += "Episodes:\n"
        for ep in self.episodes:
            my_string += f" {ep}\n"

        my_string += f"Quality: {Quality.qualityStrings[self.quality]}\n"
        my_string += f"Name: {self.name}\n"
        my_string += f"Size: {self.size}\n"
        my_string += f"Release Group: {self.release_group}\n"

        return my_string


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with a URL to the NZB
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.result_type = "nzb"


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.result_type = "nzbdata"


class TorrentSearchResult(SearchResult):
    """
    Torrent result with a URL to the torrent
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.result_type = "torrent"


class Proper(object):
    def __init__(self, name, url, date, show):
        self.name = name
        self.url = url
        self.date = date
        self.provider = None
        self.quality = Quality.UNKNOWN
        self.release_group = None
        self.version = -1

        self.show = show
        self.indexer = None
        self.indexerid = -1
        self.season = -1
        self.episode = -1
        self.scene_season = -1
        self.scene_episode = -1

    def __str__(self):
        return "{date} {name} {season}x{episode} of {series_id} from {indexer}".format(
            date=self.date, name=self.name, season=self.season, episode=self.episode, series_id=self.indexerid, indexer=sickchill.indexer.name(self.indexer)
        )


class ErrorViewer(object):
    """
    Keeps a static list of UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    errors = []

    def __init__(self):
        ErrorViewer.errors = []

    @staticmethod
    def add(error):
        ErrorViewer.errors = [e for e in ErrorViewer.errors if e.message != error.message]
        ErrorViewer.errors.append(error)

    @staticmethod
    def clear():
        ErrorViewer.errors = []

    @staticmethod
    def get():
        return ErrorViewer.errors


class WarningViewer(object):
    """
    Keeps a static list of (warning) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    errors = []

    def __init__(self):
        WarningViewer.errors = []

    @staticmethod
    def add(error):
        WarningViewer.errors = [e for e in WarningViewer.errors if e.message != error.message]
        WarningViewer.errors.append(error)

    @staticmethod
    def clear():
        WarningViewer.errors = []

    @staticmethod
    def get():
        return WarningViewer.errors


class UIError(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.title = sys.exc_info()[-2] or message
        self.message = message
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
