# Author: duramato <matigonkas@outlook.com>
# Author: miigotu
# URL: https://github.com/SiCKRAGETV/sickrage
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
import traceback
import xmltodict
from xml.parsers.expat import ExpatError

from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard.common import USER_AGENT
from sickbeard.providers import generic


class ExtraTorrentProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "ExtraTorrent")

        self.urls = {
            'index': 'http://extratorrent.cc',
            'rss': 'http://extratorrent.cc/rss.xml',
            }

        self.url = self.urls['index']

        self.supportsBacklog = True
        self.public = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = ExtraTorrentCache(self)
        self.headers.update({'User-Agent': USER_AGENT})
        self.search_params = {'cid': 8}

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                try:
                    self.search_params.update({'type': ('search', 'rss')[mode is 'RSS'], 'search': search_string})
                    data = self.getURL(self.urls['rss'], params=self.search_params)
                    if not data:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    try:
                        data = xmltodict.parse(data)
                    except ExpatError:
                        logger.log(u"Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data), logger.ERROR)
                        continue

                    if not all([data, 'rss' in data, 'channel' in data['rss'], 'item' in data['rss']['channel']]):
                        logger.log(u"Malformed rss returned, skipping", logger.DEBUG)
                        continue

                    # https://github.com/martinblech/xmltodict/issues/111
                    entries = data['rss']['channel']['item']
                    entries = entries if isinstance(entries, list) else [entries]

                    for item in entries:
                        title = item['title'].decode('utf-8')
                       # info_hash = item['info_hash']
                        size = int(item['size'])
                        seeders = helpers.tryInt(item['seeders'], 0)
                        leechers = helpers.tryInt(item['leechers'], 0)
                        download_url = item['enclosure']['@url'] if 'enclosure' in item else self._magnet_from_details(item['link'])

                        if not all([title, download_url]):
                            continue

                            # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode is not 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode is not 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _magnet_from_details(self, link):
        details = self.getURL(link)
        if not details:
            return ''

        match = re.search(r'href="(magnet.*?)"', details)
        if not match:
            return ''

        return match.group(1)

    def seedRatio(self):
        return self.ratio


class ExtraTorrentCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = ExtraTorrentProvider()
