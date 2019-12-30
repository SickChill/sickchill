# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
#
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import sys

from six.moves import urllib

import sickbeard
import sickchill
from sickbeard.common import Quality, USER_AGENT
from sickchill.helper.common import dateTimeFormat


class SickBeardURLopener(urllib.request.FancyURLopener, object):
    version = USER_AGENT


class SearchResult(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """
    Represents a search result from an indexer.
    """

    def __init__(self, episodes):
        self.provider = None

        # release show object
        self.show = None

        # URL to the NZB/torrent file
        self.url = ''

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # list of TVEpisode objects that this result is associated with
        self.episodes = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # release name
        self.name = ''

        # size of the release (-1 = n/a)
        self.size = -1

        # release group
        self.release_group = ''

        # version
        self.version = -1

        # hash
        self.hash = None

        # content
        self.content = None

        self.resultType = ''

    def from_json(self, result_dict):
        self.name = result_dict.get('title')
        self.hash = result_dict.get('hash')
        self.url = result_dict.get('link')
        self.size = result_dict.get('size')
        self.version = result_dict.get('version')
        self.release_group = result_dict.get('release_group')
        self.quality = result_dict.get('quality')
        self.provider = sickbeard.providers.getProviderModule(result_dict.get('provider')).provider

    @classmethod
    def make_result(cls, result_dict):
        show = sickbeard.tv.Show.find(sickbeard.showList, int(result_dict.get('show')))
        episode = show.getEpisode(result_dict.get('season'), result_dict.get('episode'))
        result = cls([episode])
        result.from_json(result_dict)
        return result

    def __str__(self):

        if self.provider is None:
            return 'Invalid provider, unable to print self'

        my_string = '{0} @ {1}\n'.format(self.provider.name, self.url)
        my_string += 'Extra Info:\n'
        for extra in self.extraInfo:
            my_string += ' {0}\n'.format(extra)

        my_string += 'Episodes:\n'
        for ep in self.episodes:
            my_string += ' {0}\n'.format(ep)

        my_string += 'Quality: {0}\n'.format(Quality.qualityStrings[self.quality])
        my_string += 'Name: {0}\n'.format(self.name)
        my_string += 'Size: {0}\n'.format(self.size)
        my_string += 'Release Group: {0}\n'.format(self.release_group)

        return my_string


class NZBSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    Regular NZB result with an URL to the NZB
    """
    def __init__(self, episodes):
        super(NZBSearchResult, self).__init__(episodes)
        self.resultType = 'nzb'


class NZBDataSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """
    def __init__(self, episodes):
        super(NZBDataSearchResult, self).__init__(episodes)
        self.resultType = 'nzbdata'


class TorrentSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    Torrent result with an URL to the torrent
    """
    def __init__(self, episodes):
        super(TorrentSearchResult, self).__init__(episodes)
        self.resultType = 'torrent'


class Proper(object):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
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
        return '{date} {name} {season}x{episode} of {series_id} from {indexer}'.format(
            date=self.date, name=self.name, season=self.season, episode=self.episode,
            series_id=self.indexerid, indexer=sickchill.indexer.name(self.indexer))


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


class UIError(object):  # pylint: disable=too-few-public-methods
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.title = sys.exc_info()[-2] or message
        self.message = message
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
