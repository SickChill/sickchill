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

import traceback
from urllib import urlencode

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BitCannonProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "BitCannon")

        self.public = True

        self.minseed = None
        self.minleech = None
        self.ratio = 0
        self.custom_url = None
        self.api_key = None

        self.cache = tvcache.TVCache(self, search_params={'RSS': ['tv', 'anime']})

        self.search_params = {
            'q': '',
            'category': 'tv',
            'apiKey': ''
        }

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        # search_strings comes in one of these formats:
        #      {'Episode': ['Italian Works S05E10']}
        #      {'Season': ['Italian Works S05']}
        #      {'RSS': ['tv', 'anime']}
        results = []

        # select the correct category (TODO:  Add more categories?)
        anime = (self.show and self.show.anime) or (ep_obj and ep_obj.show and ep_obj.show.anime) or False
        self.search_params['category'] = ('tv', 'anime')[anime]

        # Set API Key (if applicable)
        if self.api_key:
            self.search_params['apiKey'] = self.api_key

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                self.search_params['q'] = search_string.encode('utf-8') if mode != 'RSS' else ''
                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                try:
                    url = "http://localhost:3000/"    # a default
                    if self.custom_url is not None:
                        if not self.custom_url.endswith('/'):
                            self.custom_url += '/'
                        url = self.custom_url
                    search_url = url + "api/search?" + urlencode(self.search_params)
                    logger.log(u"Search URL: %s" % search_url, logger.DEBUG)
                    parsed_json = self.get_url(search_url, json=True)

                    if not parsed_json:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    if self._check_auth_from_data(parsed_json):
                        try:
                            found_torrents = parsed_json['torrents']
                        except Exception:
                            found_torrents = {}

                        for result in found_torrents:
                            try:
                                title = result.get('title', '')
                                info_hash = result.get('infoHash', '')
                                swarm = result.get('swarm', None)
                                if swarm is not None:
                                    seeders = int(swarm.get('seeders', 0))
                                    leechers = int(swarm.get('leechers', 0))
                                torrent_size = result.get('size', 0)
                                size = convert_size(torrent_size) or -1
                                download_url = "magnet:?xt=urn:btih:" + info_hash

                            except (AttributeError, TypeError, KeyError, ValueError):
                                continue

                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
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

    @staticmethod
    def _check_auth_from_data(data):
        if data and hasattr(data, 'status') and hasattr(data, 'message'):
            if data and data['status'] == 401 and data['message'] == 'Invalid API key':
                logger.log(u"Invalid api key. Check your settings", logger.WARNING)
                return False

        return True

provider = BitCannonProvider()
