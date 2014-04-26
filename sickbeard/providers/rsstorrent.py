# Author: Mr_Orange
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.


import os
import re
import urlparse

import sickbeard
import generic

from sickbeard import helpers
from sickbeard import encodingKludge as ek
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import clients
from sickbeard.exceptions import ex

from lib import requests
from lib.requests import exceptions
from lib.bencode import bdecode
from lib.feedparser import feedparser

class TorrentRssProvider(generic.TorrentProvider):
    def __init__(self, name, url):
        generic.TorrentProvider.__init__(self, name)
        self.cache = TorrentRssCache(self)
        self.url = re.sub('\/$', '', url)
        self.enabled = True
        self.supportsBacklog = False

    def configStr(self):
        return self.name + '|' + self.url + '|' + str(int(self.enabled))

    def imageName(self):
        if ek.ek(os.path.isfile, ek.ek(os.path.join, sickbeard.PROG_DIR, 'data', 'images', 'providers', self.getID() + '.png')):
            return self.getID() + '.png'
        return 'torrentrss.png'

    def isEnabled(self):
        return self.enabled

    def _get_title_and_url(self, item):

        title, url = None, None

        title = item.title

        attempt_list = [lambda: item.torrent_magneturi,

                        lambda: item.enclosures[0].href,

                        lambda: item.link]

        for cur_attempt in attempt_list:
            try:
                url = cur_attempt()
            except:
                continue

            if title and url:
                return (title, url)

        return (title, url)

    def validateRSS(self):

        try:

            data = self.cache._getRSSData()

            if not data:
                return (False, 'No data returned from url: ' + self.url)

            items = data.entries
            if not len(items) > 0:
                return (False, 'No items found in the RSS feed ' + self.url)

            (title, url) = self._get_title_and_url(items[0])

            if not title:
                return (False, 'Unable to get title from first item')

            if not url:
                return (False, 'Unable to get torrent url from first item')

            if url.startswith('magnet:') and re.search('urn:btih:([\w]{32,40})', url):
                return (True, 'RSS feed Parsed correctly')
            else:
                torrent_file = self.getURL(url)
                try:
                    bdecode(torrent_file)
                except Exception, e:
                    self.dumpHTML(torrent_file)
                    return (False, 'Torrent link is not a valid torrent file: ' + ex(e))

            return (True, 'RSS feed Parsed correctly')

        except Exception, e:
            return (False, 'Error when trying to load RSS: ' + ex(e))

    def getURL(self, url, post_data=None, headers=None):
        try:
            parsed = list(urlparse.urlparse(url))
            parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one
            response = requests.get(url, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u"Error loading " + self.name + " URL: " + ex(e), logger.ERROR)
            return None

        if response.status_code != 200:
            logger.log(self.name + u" page requested with url " + url + " returned status code is " + str(
                response.status_code) + ': ' + clients.http_error_code[response.status_code], logger.WARNING)
            return None

        return response.content

    def dumpHTML(self, data):

        dumpName = ek.ek(os.path.join, sickbeard.CACHE_DIR, 'custom_torrent.html')

        try:
            fileOut = open(dumpName, 'wb')
            fileOut.write(data)
            fileOut.close()
            helpers.chmodAsParent(dumpName)
        except IOError, e:
            logger.log("Unable to save the file: " + ex(e), logger.ERROR)
            return False
        logger.log(u"Saved custom_torrent html dump " + dumpName + " ", logger.MESSAGE)
        return True


class TorrentRssCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)
        self.minTime = 15

    def _getRSSData(self):
        url = self.provider.url
        logger.log(u"TorrentRssCache cache update URL: " + self.provider.url, logger.DEBUG)
        return self.provider.getRSSFeed(url)

    def _parseItem(self, item):

        (title, url) = self.provider._get_title_and_url(item)
        if not title or not url:
            logger.log(u"The XML returned from the RSS feed is incomplete, this result is unusable", logger.ERROR)
            return None

        logger.log(u"Adding item from RSS to cache: " + title, logger.DEBUG)
        return self._addCacheEntry(title, url)