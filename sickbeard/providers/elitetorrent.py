# coding=utf-8
# Author: CristianBB
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

import re
from six.moves import urllib
import traceback

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class elitetorrentProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "EliteTorrent")

        self.onlyspasearch = None
        self.minseed = None
        self.minleech = None
        self.cache = tvcache.TVCache(self)  # Only poll EliteTorrent every 20 minutes max

        self.urls = {
            'base_url': 'http://www.elitetorrent.net',
            'search': 'http://www.elitetorrent.net/torrents.php'
        }

        self.url = self.urls['base_url']

        """
        Search query:
        http://www.elitetorrent.net/torrents.php?cat=4&modo=listado&orden=fecha&pag=1&buscar=fringe

        cat = 4 => Shows
        modo = listado => display results mode
        orden = fecha => order
        buscar => Search show
        pag = 1 => page number
        """

        self.search_params = {
            'cat': 4,
            'modo': 'listado',
            'orden': 'fecha',
            'pag': 1,
            'buscar': ''

        }

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        results = []
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                logger.log(u"Show info is not spanish, skipping provider search", logger.DEBUG)
                continue

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: {search}".format(search=search_string.decode('utf-8')),
                               logger.DEBUG)

                search_string = re.sub(r'S0*(\d*)E(\d*)', r'\1x\2', search_string)
                self.search_params['buscar'] = search_string.strip() if mode != 'RSS' else ''

                search_url = self.urls['search'] + '?' + urllib.parse.urlencode(self.search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url, timeout=30)
                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find('table', class_='fichas-listado')
                        torrent_rows = []

                        if torrent_table is not None:
                            torrent_rows = torrent_table.findAll('tr')

                        if not torrent_rows:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for row in torrent_rows[1:]:
                            try:
                                download_url = self.urls['base_url'] + row.find('a')['href']
                                title = self._processTitle(row.find('a', class_='nombre')['title'])
                                seeders = try_int(row.find('td', class_='semillas').get_text(strip=True))
                                leechers = try_int(row.find('td', class_='clientes').get_text(strip=True))

                                # Provider does not provide size
                                size = -1

                            except (AttributeError, TypeError, KeyError, ValueError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    @staticmethod
    def _processTitle(title):

        # Quality, if no literal is defined it's HDTV
        if 'calidad' not in title:
            title += ' HDTV x264'

        title = title.replace('(calidad baja)', 'HDTV x264')
        title = title.replace('(Buena calidad)', '720p HDTV x264')
        title = title.replace('(Alta calidad)', '720p HDTV x264')
        title = title.replace('(calidad regular)', 'DVDrip x264')
        title = title.replace('(calidad media)', 'DVDrip x264')

        # Language, all results from this provider have spanish audio, we append it to title (avoid to download undesired torrents)
        title += ' SPANISH AUDIO'
        title += '-ELITETORRENT'

        return title.strip()

provider = elitetorrentProvider()
