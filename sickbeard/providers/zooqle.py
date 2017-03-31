# coding=utf-8
# Author: sharkykh
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

from __future__ import unicode_literals

import validators
from requests.compat import urljoin
from sickbeard.bs4_parser import BS4Parser

import sickbeard
from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class ZooqleProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes
    """ Provider for Zooqle.com """
    def __init__(self):

        TorrentProvider.__init__(self, 'Zooqle')

        self.public = True

        self.confirmed = True
        self.minseed = None
        self.minleech = None

        self.urls = {'search': 'https://zooqle.com/search'}

        self.custom_url = None

        # self.cache = tvcache.TVCache(self, search_params={'RSS': ['tv', 'anime']})  # ??????????????????
        self.cache = tvcache.TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        """ Search provider """
        results = []

        anime = (self.show and self.show.anime) or (ep_obj and ep_obj.show and ep_obj.show.anime) or False
        search_params = {
            'q': '%s category:' + ('tv', 'anime')[anime],
            'fmt': 'rss',
            'pg': 1  # page number
        }

        for mode in search_strings:
            if mode == 'RSS':
                logger.log("RSS search mode is not supported, skipping".format(mode), logger.DEBUG)
                continue

            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                search_params['q'] %= search_string
                logger.log('Search string: {0}'.format(search_string.decode('utf-8')), logger.DEBUG)

                search_url = self.urls['search']
                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log('Invalid custom url: {0}'.format(self.custom_url), logger.WARNING)
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                data = self.get_url(search_url, params=search_params, returns='text')
                if not data:
                    logger.log('URL did not return results/data, if the results are on the site maybe try a custom url,'
                               ' or a different one', logger.DEBUG)
                    continue

                if not data.startswith('<?xml'):
                    logger.log('Expected xml but got something else, is your mirror failing?', logger.INFO)
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    results_count = int(html.find('opensearch:totalresults').text)
                    items_per_page = int(html.find('opensearch:itemsperpage').text)

                    if float(results_count)/float(items_per_page) > 1:
                        logger.log('Multiple pages of results were received from provider. '
                                   'Pagination is not supported yet, using results from page one only', logger.DEBUG)

                    for item in html('item'):
                        try:
                            title = item.title.get_text(strip=True)
                            download_url = item.find('torrent:magneturi').next.replace('CDATA', '').strip('[!]') + \
                                           self._custom_trackers
                            if sickbeard.TORRENT_METHOD == 'blackhole':
                                download_url = item.enclosure['url']

                            if not (title and download_url):
                                continue

                            seeders = try_int(item.find('torrent:seeds').get_text(strip=True))
                            leechers = try_int(item.find('torrent:peers').get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or "
                                           "leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            verified = bool(try_int(item.find('torrent:verified').get_text(strip=True)))
                            if self.confirmed and not verified:
                                logger.log('Found result ' + title + " but that doesn't seem like a verified result so "
                                                                     "I'm ignoring it", logger.DEBUG)
                                continue

                            torrent_size = item.find('torrent:contentlength').get_text(strip=True)
                            size = convert_size(torrent_size) or -1
                            info_hash = item.find('torrent:infohash').get_text(strip=True)

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                            logger.log('Found result: {0} with {1} seeders and {2} leechers'.format(title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = ZooqleProvider()
