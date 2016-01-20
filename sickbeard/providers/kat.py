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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import posixpath  # Must use posixpath
import traceback
from urllib import urlencode
from bs4 import BeautifulSoup

import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import try_int, convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class KatProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes
    def __init__(self):

        TorrentProvider.__init__(self, "KickAssTorrents")

        self.public = True

        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {
            'base_url': 'https://kat.cr/',
            'search': 'https://kat.cr/%s/',
        }

        self.url = self.urls['base_url']
        self.custom_url = None

        self.headers.update({'User-Agent': USER_AGENT})

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

        self.cache = KatCache(self)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []

        # select the correct category
        anime = (self.show and self.show.anime) or (ep_obj and ep_obj.show and ep_obj.show.anime) or False
        self.search_params['category'] = ('tv', 'anime')[anime]

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                self.search_params['q'] = search_string.encode('utf-8') if mode != 'RSS' else ''
                self.search_params['field'] = 'seeders' if mode != 'RSS' else 'time_add'

                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                url_fmt_string = 'usearch' if mode != 'RSS' else search_string
                try:
                    search_url = self.urls['search'] % url_fmt_string + '?' + urlencode(self.search_params)
                    if self.custom_url:
                        search_url = posixpath.join(self.custom_url, search_url.split(self.url)[1].lstrip('/'))  # Must use posixpath

                    logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
                    data = self.get_url(search_url)
                    if not data:
                        logger.log(u'URL did not return data, maybe try a custom url, or a different one', logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    data = BeautifulSoup(data, 'html5lib')

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

                            seeders = try_int(item.find('torrent:seeds').text)
                            leechers = try_int(item.find('torrent:peers').text)
                            verified = bool(try_int(item.find('torrent:verified').text))
                            torrent_size = item.find('torrent:contentlength').text
                            size = convert_size(torrent_size) or -1

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
                            logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                        items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio


class KatCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['tv', 'anime']}
        return {'entries': self.provider.search(search_params)}

provider = KatProvider()
