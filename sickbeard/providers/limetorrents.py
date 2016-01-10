# coding=utf-8
# Author: Gonçalo (aka duramato/supergonkas) <matigonkas@outlook.com>
# URL: https://github.com/SickRage/sickrage
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
from bs4 import BeautifulSoup
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import try_int, convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class LimeTorrentsProvider(TorrentProvider): # pylint: disable=too-many-instance-attributes
    def __init__(self):
        TorrentProvider.__init__(self, "LimeTorrents")

        self.urls = {
            'index': 'https://www.limetorrents.cc/',
            'search': 'https://www.limetorrents.cc/searchrss/20/',
            'rss': 'https://www.limetorrents.cc/rss/20/'
            }

        self.url = self.urls['index']

        self.public = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.headers.update({'User-Agent': USER_AGENT})
        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        self.cache = LimeTorrentsCache(self)

    def search(self, search_strings, age=0, ep_obj=None): # pylint: disable=too-many-branches,too-many-locals
        results = []
        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                try:
                    url = (self.urls['rss'], self.urls['search'] + search_string)[mode != 'RSS']
                    logger.log(u"URL: %r " % url, logger.DEBUG)
                    data = self.get_url(url)
                    if not data:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    if not data.startswith('<?xml'):
                        logger.log(u'Expected xml but got something else, is your mirror failing?', logger.INFO)
                        continue

                    data = BeautifulSoup(data, 'html5lib')

                    entries = data.findAll('item')
                    if not entries:
                        logger.log(u'Returned xml contained no results', logger.INFO)
                        continue

                    for item in entries:
                        try:
                            title = item.title.text
                            download_url = item.enclosure['url']

                            if not (title and download_url):
                                continue
                            #seeders and leechers are presented diferently when doing a search and when looking for newly added
                            if mode == 'RSS':
                                # <![CDATA[
                                # Category: <a href="http://www.limetorrents.cc/browse-torrents/TV-shows/">TV shows</a><br /> Seeds: 1<br />Leechers: 0<br />Size: 7.71 GB<br /><br /><a href="http://www.limetorrents.cc/Owen-Hart-of-Gold-Djon91-torrent-7180661.html">More @ limetorrents.cc</a><br />
                                # ]]>
                                description = item.find('description')
                                seeders = try_int(description.find_all('br')[0].next_sibling.strip().lstrip('Seeds: '))
                                leechers = try_int(description.find_all('br')[1].next_sibling.strip().lstrip('Leechers: '))
                            else:
                                #<description>Seeds: 6982 , Leechers 734</description>
                                description = item.find('description').text.partition(',')
                                seeders = try_int(description[0].lstrip('Seeds: ').strip())
                                leechers = try_int(description[2].lstrip('Leechers ').strip())

                            torrent_size = item.find('size').text

                            size = convert_size(torrent_size) or -1

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

                            # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items.append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio


class LimeTorrentsCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['rss']}
        return {'entries': self.provider.search(search_strings)}


provider = LimeTorrentsProvider()
