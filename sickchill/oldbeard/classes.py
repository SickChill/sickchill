import datetime
import sys

import sickchill
from sickchill.helper.common import dateTimeFormat

from .common import Quality


class SearchResult(object):
    """
    Represents a search result from an indexer.
    """

    def __init__(self, episodes):
        self.provider = None

        # release show object
        self.show = None

        # URL to the NZB/torrent file
        self.url = ""

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # list of TVEpisode objects that this result is associated with
        self.episodes = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # release name
        self.name = ""

        # size of the release (-1 = n/a)
        self.size = -1

        # release group
        self.release_group = ""

        # version
        self.version = -1

        # hash
        self.hash = None

        # content
        self.content = None

        self.resultType = ""

        self.priority = 0

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
        show = sickchill.show.Show.Show._validate_indexer_id(result_dict.get("indexerid"))
        if not show[1]:
            return show[0]

        show = show[1]
        episode_objects = [show.getEpisode(result_dict.get("season"), ep) for ep in result_dict.get("episodes").split("|") if ep]
        result = cls(episode_objects)
        result.from_json(result_dict)
        result.show = show

        return result

    def __str__(self):

        if self.provider is None:
            return "Invalid provider, unable to print self"

        my_string = "{0} @ {1}\n".format(self.provider.name, self.url)
        my_string += "Extra Info:\n"
        for extra in self.extraInfo:
            my_string += " {0}\n".format(extra)

        my_string += "Episodes:\n"
        for ep in self.episodes:
            my_string += " {0}\n".format(ep)

        my_string += "Quality: {0}\n".format(Quality.qualityStrings[self.quality])
        my_string += "Name: {0}\n".format(self.name)
        my_string += "Size: {0}\n".format(self.size)
        my_string += "Release Group: {0}\n".format(self.release_group)

        return my_string


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with an URL to the NZB
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.resultType = "nzb"


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.resultType = "nzbdata"


class TorrentSearchResult(SearchResult):
    """
    Torrent result with an URL to the torrent
    """

    def __init__(self, episodes):
        super().__init__(episodes)
        self.resultType = "torrent"


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
