# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

import traceback
from bs4 import BeautifulSoup

import sickbeard
from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BitSnoopProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "BitSnoop")

        self.urls = {
            'index': 'http://bitsnoop.com',
            'search': 'http://bitsnoop.com/search/video/',
            'rss': 'http://bitsnoop.com/new_video.html?fmt=rss'
        }

        self.url = self.urls['index']

        self.public = True
        self.minseed = None
        self.minleech = None

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = tvcache.TVCache(self, search_params={'RSS': ['rss']})

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches,too-many-locals
        results = []
        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format(search_string.decode("utf-8")),
                               logger.DEBUG)

                try:
                    search_url = (self.urls['rss'], self.urls['search'] + search_string + '/s/d/1/?fmt=rss')[mode != 'RSS']

                    data = self.get_url(search_url, returns='text')
                    if not data:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    data = BeautifulSoup(data, 'html5lib')
                    for item in data.findAll('item'):
                        try:
                            if not item.category.text.endswith(('TV', 'Anime')):
                                continue

                            title = item.title.text
                            assert isinstance(title, unicode)
                            # Use the torcache link bitsnoop provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item.enclosure['url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'torcache' not in download_url:
                                download_url = item.find('magneturi').next.replace('CDATA', '').strip('[]') + self._custom_trackers

                            if not (title and download_url):
                                continue

                            seeders = try_int(item.find('numseeders').text)
                            leechers = try_int(item.find('numleechers').text)
                            torrent_size = item.find('size').text
                            size = convert_size(torrent_size) or -1

                            info_hash = item.find('infohash').text

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                            # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                        if mode != 'RSS':
                            logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                        items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = BitSnoopProvider()
