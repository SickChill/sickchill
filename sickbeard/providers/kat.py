# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: http://sickrage.github.io
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


import traceback

from urllib import urlencode
from bs4 import BeautifulSoup

import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickbeard.providers import generic
from sickbeard.helpers import tryInt

class KATProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "KickAssTorrents")

        self.supportsBacklog = True
        self.public = True

        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None


        self.urls = {
            'base_url': 'https://kickass.unblocked.pe/',
            'search': 'https://kickass.unblocked.pe/%s/',
        }

        self.url = self.urls['base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

        self.cache = KATCache(self)


    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # select the correct category
        anime = (self.show and self.show.anime) or (epObj and epObj.show and epObj.show.anime) or False
        self.search_params['category'] = ('tv', 'anime')[anime]

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                self.search_params['q'] = search_string.encode('utf-8') if mode != 'RSS' else ''
                self.search_params['field'] = 'seeders' if mode != 'RSS' else 'time_add'

                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                url_fmt_string = 'usearch' if mode != 'RSS' else search_string
                try:
                    searchURL = self.urls['search'] % url_fmt_string + '?' + urlencode(self.search_params)
                    logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                    data = self.getURL(searchURL)
                    # data = self.getURL(self.urls[('search', 'rss')[mode is 'RSS']], params=self.search_params)
                    if not data:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    data = BeautifulSoup(data, features=["html5lib", "permissive"])

                    entries = data.findAll('item')
                    for item in entries:
                        try:
                            title = item.title.text
                            assert isinstance(title, unicode)
                            # Use the torcache link kat provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item.enclosure['url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'torcache' not in download_url:
                                download_url = item.find('torrent:magneturi').next.replace('CDATA', '').strip('[]')

                            if not (title and download_url):
                                continue

                            seeders = tryInt(item.find('torrent:seeds').text, 0)
                            leechers = tryInt(item.find('torrent:peers').text, 0)
                            verified = bool(tryInt(item.find('torrent:verified').text, 0))
                            size = tryInt(item.find('torrent:contentlength').text)

                            info_hash = item.find('torrent:infohash').text
                            # link = item['link']

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue


                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        if self.confirmed and not verified:
                            if mode != 'RSS':
                                logger.log(u"Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers, info_hash
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class KATCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['tv', 'anime']}
        return {'entries': self.provider._doSearch(search_params)}

provider = KATProvider()
