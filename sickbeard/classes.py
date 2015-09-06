# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
import re
import sys

import sickbeard

import urllib
import datetime
from dateutil import parser

from common import USER_AGENT, Quality


class SickBeardURLopener(urllib.FancyURLopener):
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
        """

        # if this is the first try then provide a username/password
        if self.numTries == 0:
            self.numTries = 1
            return (self.username, self.password)

        # if we've tried before then return blank which cancels the request
        else:
            return ('', '')

    # this is pretty much just a hack for convenience
    def openit(self, url):
        self.numTries = 0
        return SickBeardURLopener.open(self, url)


class SearchResult:
    """
    Represents a search result from an indexer.
    """

    def __init__(self, episodes):
        self.provider = -1

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

    def __str__(self):

        if self.provider is None:
            return "Invalid provider, unable to print self"

        myString = self.provider.name + " @ " + self.url + "\n"
        myString += "Extra Info:\n"
        for extra in self.extraInfo:
            myString += "  " + extra + "\n"

        myString += "Episode: " + str(self.episodes) + "\n"
        myString += "Quality: " + Quality.qualityStrings[self.quality] + "\n"
        myString += "Name: " + self.name + "\n"
        myString += "Size: " + str(self.size) + "\n"
        myString += "Release Group: " + str(self.release_group) + "\n"

        return myString

    def fileName(self):
        return self.episodes[0].prettyName() + "." + self.resultType


class NZBSearchResult(SearchResult):
    """
    Regular NZB result with an URL to the NZB
    """
    resultType = "nzb"


class NZBDataSearchResult(SearchResult):
    """
    NZB result where the actual NZB XML data is stored in the extraInfo
    """
    resultType = "nzbdata"


class TorrentSearchResult(SearchResult):
    """
    Torrent result with an URL to the torrent
    """
    resultType = "torrent"


class AllShowsListUI:
    """
    This class is for indexer api. Instead of prompting with a UI to pick the
    desired result out of a list of shows it tries to be smart about it
    based on what shows are in SB.
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries):
        searchResults = []
        seriesnames = []

        # get all available shows
        if allSeries:
            if 'searchterm' in self.config:
                searchterm = self.config['searchterm']
                # try to pick a show that's in my show list
                for curShow in allSeries:
                    if curShow in searchResults:
                        continue

                    if 'seriesname' in curShow:
                        seriesnames.append(curShow['seriesname'])
                    if 'aliasnames' in curShow:
                        seriesnames.extend(curShow['aliasnames'].split('|'))

                    for name in seriesnames:
                        if searchterm.lower() in name.lower():
                            if 'firstaired' not in curShow:
                                curShow['firstaired'] = str(datetime.date.fromordinal(1))
                                curShow['firstaired'] = re.sub("([-]0{2}){1,}", "", curShow['firstaired'])
                                fixDate = parser.parse(curShow['firstaired'], fuzzy=True).date()
                                curShow['firstaired'] = fixDate.strftime("%Y-%m-%d")

                            if curShow not in searchResults:
                                searchResults += [curShow]

        return searchResults


class ShowListUI:
    """
    This class is for tvdb-api. Instead of prompting with a UI to pick the
    desired result out of a list of shows it tries to be smart about it
    based on what shows are in SB. 
    """

    def __init__(self, config, log=None):
        self.config = config
        self.log = log

    def selectSeries(self, allSeries):
        try:
            # try to pick a show that's in my show list
            for curShow in allSeries:
                if filter(lambda x: int(x.indexerid) == int(curShow['id']), sickbeard.showList):
                    return curShow
        except:
            pass

        # if nothing matches then return first result
        return allSeries[0]


class Proper:
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
        return str(self.date) + " " + self.name + " " + str(self.season) + "x" + str(self.episode) + " of " + str(
            self.indexerid) + " from " + str(sickbeard.indexerApi(self.indexer).name)


class ErrorViewer():
    """
    Keeps a static list of UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    errors = []

    def __init__(self):
        ErrorViewer.errors = []

    @staticmethod
    def add(error):
        ErrorViewer.errors.append(error)

    @staticmethod
    def clear():
        ErrorViewer.errors = []

    @staticmethod
    def get():
        return ErrorViewer.errors


class UIError():
    """
    Represents an error to be displayed in the web UI.
    """

    def __init__(self, message):
        self.title = sys.exc_info()[-2] or message
        self.message = message
        self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
