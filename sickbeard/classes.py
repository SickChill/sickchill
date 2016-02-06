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
import re
import sys
import urllib

from dateutil import parser

import sickbeard
from sickbeard.common import USER_AGENT, Quality

from sickrage.helper.common import dateFormat, dateTimeFormat


class SickBeardURLopener(urllib.FancyURLopener, object):
    version = USER_AGENT


class AuthURLOpener(SickBeardURLopener):
    """
    URLOpener class that supports http auth without needing interactive password entry.
    If the provided username/password don't work it simply fails.

    user: username to use for HTTP auth
    pw: password to use for HTTP auth
    """

    def __init__(self, user, pw):
        self.username = user
        self.password = pw

        # remember if we've tried the username/password before
        self.numTries = 0

        # call the base class
        urllib.FancyURLopener.__init__(self)

    def prompt_user_passwd(self, host, realm):
        """
        Override this function and instead of prompting just give the
        username/password that were provided when the class was instantiated.

        :param host:
        :param realm:
        """

        # if this is the first try then provide a username/password
        if self.numTries == 0:
            self.numTries = 1
            return self.username, self.password

        # if we've tried before then return blank which cancels the request
        else:
            return u'', u''

    # this is pretty much just a hack for convenience
    def openit(self, url):
        self.numTries = 0
        return SickBeardURLopener.open(self, url)


class SearchResult(object):
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

        my_string = u'{provider} @ {url}\n'.format(provider=self.provider.name, url=self.url)
        my_string += u'Extra Info:\n'
        for extra in self.extraInfo:
            my_string += u' {info}\n'.format(info=extra)

        my_string += u'Episodes:\n'
        for ep in self.episodes:
            my_string += u' {episode}\n'.format(episode=ep)

        my_string += u'Quality: {quality}\n'.format(quality=Quality.qualityStrings[self.quality])
        my_string += u'Name: {name}\n'.format(name=self.name)
        my_string += u'Size: {size}\n'.format(size=self.size)
        my_string += u'Release Group: {group}\n'.format(group=self.release_group)

        return my_string

    def fileName(self):
        return u'{name}.{type}'.format(name=self.episodes[0].prettyName(), type=self.resultType)


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with an URL to the NZB
    """
    def __init__(self, episodes):
        super(NZBSearchResult, self).__init__(episodes)
        self.resultType = u'nzb'


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """
    def __init__(self, episodes):
        super(NZBDataSearchResult, self).__init__(episodes)
        self.resultType = u'nzbdata'


class TorrentSearchResult(SearchResult):
    """
    Torrent result with an URL to the torrent
    """
    def __init__(self, episodes):
        super(TorrentSearchResult, self).__init__(episodes)
        self.resultType = u'torrent'


class AllShowsListUI(object):
    """
    This class is for indexer api.

    Instead of prompting with a UI to pick the desired result out of a
    list of shows it tries to be smart about it based on what shows
    are in SickRage.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries):
        search_results = []
        series_names = []

        # get all available shows
        if allSeries:
            if 'searchterm' in self.config:
                search_term = self.config['searchterm']
                # try to pick a show that's in my show list
                for curShow in allSeries:
                    if curShow in search_results:
                        continue

                    if 'seriesname' in curShow:
                        series_names.append(curShow['seriesname'])
                    if 'aliasnames' in curShow:
                        series_names.extend(curShow['aliasnames'].split('|'))

                    for name in series_names:
                        if search_term.lower() in name.lower():
                            if 'firstaired' not in curShow:
                                curShow['firstaired'] = str(datetime.date.fromordinal(1))
                                curShow['firstaired'] = re.sub("([-]0{2})+", "", curShow['firstaired'])
                                fix_date = parser.parse(curShow['firstaired'], fuzzy=True).date()
                                curShow['firstaired'] = fix_date.strftime(dateFormat)

                            if curShow not in search_results:
                                search_results += [curShow]

        return search_results


class ShowListUI(object):
    """
    This class is for tvdb-api.

    Instead of prompting with a UI to pick the desired result out of a
    list of shows it tries to be smart about it based on what shows
    are in SickRage.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries):
        try:
            # try to pick a show that's in my show list
            show_id_list = [int(x.indexerid) for x in sickbeard.showList]
            for curShow in allSeries:
                if int(curShow['id']) in show_id_list:
                    return curShow
        except Exception:
            pass

        # if nothing matches then return first result
        return allSeries[0]


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


class UIError(object):
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.title = sys.exc_info()[-2] or message
        self.message = message
        self.time = datetime.datetime.now().strftime(dateTimeFormat)
