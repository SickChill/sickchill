# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
#
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import datetime
import sys

import sickbeard
from sickbeard.common import Quality, USER_AGENT
from sickrage.helper.common import dateTimeFormat


from six.moves import urllib


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
        self.url = u''

        # used by some providers to store extra info associated with the result
        self.extraInfo = []

        # list of TVEpisode objects that this result is associated with
        self.episodes = episodes

        # quality of the release
        self.quality = Quality.UNKNOWN

        # release name
        self.name = u''

        # size of the release (-1 = n/a)
        self.size = -1

        # release group
        self.release_group = u''

        # version
        self.version = -1

        # hash
        self.hash = None

        # content
        self.content = None

        self.resultType = u''

    def __str__(self):

        if self.provider is None:
            return u'Invalid provider, unable to print self'

        my_string = u'{0} @ {1}\n'.format(self.provider.name, self.url)
        my_string += u'Extra Info:\n'
        for extra in self.extraInfo:
            my_string += u' {0}\n'.format(extra)

        my_string += u'Episodes:\n'
        for ep in self.episodes:
            my_string += u' {0}\n'.format(ep)

        my_string += u'Quality: {0}\n'.format(Quality.qualityStrings[self.quality])
        my_string += u'Name: {0}\n'.format(self.name)
        my_string += u'Size: {0}\n'.format(self.size)
        my_string += u'Release Group: {0}\n'.format(self.release_group)

        return my_string

    def fileName(self):
        return u'{0}.{1}'.format(self.episodes[0].prettyName(), self.resultType)


class NZBSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    Regular NZB result with an URL to the NZB
    """
    def __init__(self, episodes):
        super(NZBSearchResult, self).__init__(episodes)
        self.resultType = u'nzb'


class NZBDataSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """
    def __init__(self, episodes):
        super(NZBDataSearchResult, self).__init__(episodes)
        self.resultType = u'nzbdata'


class TorrentSearchResult(SearchResult):  # pylint: disable=too-few-public-methods
    """
    Torrent result with an URL to the torrent
    """
    def __init__(self, episodes):
        super(TorrentSearchResult, self).__init__(episodes)
        self.resultType = u'torrent'


class AllShowsListUI(object):  # pylint: disable=too-few-public-methods
    """
    This class is for indexer api.

    Instead of prompting with a UI to pick the desired result out of a
    list of shows it tries to be smart about it based on what shows
    are in SickRage.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, all_results):
        search_results = []

        # get all available shows
        if all_results and 'searchterm' in self.config:
            show_id_list = {int(x.indexerid) for x in sickbeard.showList if x}
            for curShow in all_results:
                if curShow in search_results:
                    continue

                if 'seriesname' not in curShow:
                    continue

                try:
                    # Skip it if its in our show list already
                    if int(curShow.get('id')) in show_id_list:
                        sickbeard.logger.log('Skipping {show_name} in the search results because it\'s already in your show list'.format(show_name=curShow.get(
                            'seriesname')))
                        continue
                except Exception:  # If it doesnt have an id, we cant use it anyways.
                    continue

                if 'firstaired' not in curShow:
                    curShow['firstaired'] = 'Unknown'

                if curShow not in search_results:
                    search_results += [curShow]

        return search_results


class ShowListUI(object):  # pylint: disable=too-few-public-methods
    """
    This class is for tvdb-api.

    Instead of prompting with a UI to pick the desired result out of a
    list of shows it tries to be smart about it based on what shows
    are in SickRage.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    @staticmethod
    def selectSeries(all_results):
        # try to pick a show that's in my show list
        show_id_list = {int(x.indexerid) for x in sickbeard.showList if x}
        for curShow in all_results:
            try:
                if int(curShow.get('id')) in show_id_list:
                    return curShow
            except Exception:
                pass

        # if nothing matches then return first result
        return all_results[0]


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
        return u'{date} {name} {season}x{episode} of {series_id} from {indexer}'.format(
            date=self.date, name=self.name, season=self.season, episode=self.episode,
            series_id=self.indexerid, indexer=sickbeard.indexerApi(self.indexer).name)


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
