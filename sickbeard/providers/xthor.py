# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

from __future__ import print_function, unicode_literals

from sickbeard import logger, tvcache

from sickrage.helper.common import try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class XThorProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, 'XThor')

        self.url = 'https://xthor.bz'
        self.urls = {'search': 'https://api.xthor.bz'}

        self.freeleech = None
        self.api_key = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll XThor every 10 minutes max

    def _check_auth(self):
        if self.api_key:
            return True

        logger.log('Your authentication credentials for {0} are missing, check your config.'.format(self.name), logger.WARNING)
        return False

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth:
            return results

        search_params = {
            'passkey': self.api_key
        }
        if self.freeleech:
            search_params['freeleech'] = 1

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log('Search string: ' + search_string.strip(), logger.DEBUG)
                    search_params['search'] = search_string
                else:
                    search_params.pop('search', '')

                jdata = self.get_url(self.urls['search'], params=search_params, returns='json')
                if not jdata:
                    logger.log('No data returned from provider', logger.DEBUG)
                    continue

                error_code = jdata.pop('error', {})
                if error_code.get('code'):
                    if error_code.get('code') != 2:
                        logger.log('{0}'.format(error_code.get('descr', 'Error code 2 - no description available')), logger.WARNING)
                        return results
                    continue

                account_ok = jdata.pop('user', {}).get('can_leech')
                if not account_ok:
                    logger.log('Sorry, your account is not allowed to download, check your ratio', logger.WARNING)
                    return results

                torrents = jdata.pop('torrents', None)
                if not torrents:
                    logger.log('Provider has no results for this search', logger.DEBUG)
                    continue

                for torrent in torrents:
                    try:
                        title = torrent.get('name')
                        download_url = torrent.get('download_link')
                        if not (title and download_url):
                            continue

                        seeders = torrent.get('seeders')
                        leechers = torrent.get('leechers')
                        if not seeders and mode != 'RSS':
                            logger.log('Discarding torrent because it doesn\'t meet the minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                       (title, seeders, leechers), logger.DEBUG)
                            continue

                        size = torrent.get('size') or -1
                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                        if mode != 'RSS':
                            logger.log('Found result: {0} with {1} seeders and {2} leechers'.format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except StandardError:
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


provider = XThorProvider()
