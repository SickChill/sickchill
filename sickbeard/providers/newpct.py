# coding=utf-8
# Author: CristianBB
# Greetings to Mr. Pine-apple
#
# URL: http://code.google.com/p/sickbeard/
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
import re
from six.moves import urllib

from sickbeard import helpers
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser


class newpctProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "Newpct")

        self.supportsBacklog = True
        self.onlyspasearch = None
        self.cache = newpctCache(self)

        # Unsupported
        # self.minseed = None
        # self.minleech = None

        self.urls = {
            'base_url': 'http://www.newpct.com',
            'search': 'http://www.newpct.com/buscar-descargas/'
        }

        self.url = self.urls['base_url']

        """
        Search query:
        http://www.newpct.com/buscar-descargas/cID=0&tLang=0&oBy=0&oMode=0&category_=767&subcategory_=All&idioma_=1&calidad_=All&oByAux=0&oModeAux=0&size_=0&btnb=Filtrar+Busqueda&q=the+strain

        category_=767 => Category Shows
        idioma_=1 => Language Spanish
        calidad_=All=> Quality ALL
        q => Search show
        """

        self.search_params = {
            'cID': 0,
            'tLang': 0,
            'oBy': 0,
            'oMode': 0,
            'category_': 767,
            'subcategory_': 'All',
            'idioma_': 1,
            'calidad_': 'All',
            'oByAux': 0,
            'oModeAux': 0,
            'size_': 0,
            'btnb': 'Filtrar+Busqueda',
            'q': ''
        }


    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # Only search if user conditions are true
        lang_info = '' if not epObj or not epObj.show else epObj.show.lang
        if self.onlyspasearch and lang_info != 'es':
            logger.log(u"Show info is not spanish, skipping provider search", logger.DEBUG)
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            for search_string in search_strings[mode]:
                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params.update({'q': search_string.strip()})

                logger.log(u"Search URL: %s" % self.urls['search'] + '?' + urllib.parse.urlencode(self.search_params), logger.DEBUG)
                data = self.getURL(self.urls['search'], post_data=self.search_params, timeout=30)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_tbody = html.find('tbody')

                        if not len(torrent_tbody):
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_table = torrent_tbody.findAll('tr')
                        if not len(torrent_table):
                            logger.log(u"Torrent table does not have any rows", logger.DEBUG)
                            continue

                        for row in torrent_table[:-1]:
                            try:
                                torrent_size = row.findAll('td')[2]
                                torrent_row = row.findAll('a')[0]

                                download_url = torrent_row.get('href', '')
                                size = self._convertSize(torrent_size.text)
                                title = self._processTitle(torrent_row.get('title', ''))

                                # FIXME: Provider does not provide seeders/leechers
                                seeders = 1
                                leechers = 0

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent (Unsupported)
                            # if seeders < self.minseed or leechers < self.minleech:
                            #     if mode is not 'RSS':
                            #         logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            #     continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            # For each search mode sort all the items by seeders if available (Unsupported)
            # items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self._doLogin():
            return False

        urls, filename = self._makeURL(result)

        for url in urls:
            # Search results don't return torrent files directly, it returns show sheets so we must parse showSheet to access torrent.
            data = self.getURL(url)
            url_torrent = re.search(r'http://tumejorserie.com/descargar/.+\.torrent', data, re.DOTALL).group()

            if url_torrent.startswith('http'):
                self.headers.update({'Referer': '/'.join(url_torrent.split('/')[:3]) + '/'})

            logger.log(u"Downloading a result from " + self.name + " at " + url)

            if helpers.download_file(url_torrent, filename, session=self.session, headers=self.headers):
                if self._verify_download(filename):
                    logger.log(u"Saved result to " + filename, logger.INFO)
                    return True
                else:
                    logger.log(u"Could not download %s" % url, logger.WARNING)
                    helpers.remove_file_failed(filename)

        if len(urls):
            logger.log(u"Failed to download any results", logger.WARNING)

        return False

    @staticmethod
    def _convertSize(size):
        size, modifier = size.split(' ')
        size = float(size)
        if modifier in 'KB':
            size = size * 1024
        elif modifier in 'MB':
            size = size * 1024**2
        elif modifier in 'GB':
            size = size * 1024**3
        elif modifier in 'TB':
            size = size * 1024**4
        return int(size)


    @staticmethod
    def _processTitle(title):

        # Remove "Mas informacion sobre " literal from title
        title = title[22:]

        # Quality
        title = title.replace('[HDTV]', '[720p HDTV x264]')
        title = title.replace('[HDTV 720p AC3 5.1]', '[720p HDTV x264]')
        title = title.replace('[HDTV 1080p AC3 5.1]', '[1080p HDTV x264]')
        title = title.replace('[DVDRIP]', '[DVDrip x264]')
        title = title.replace('[DVD Rip]', '[DVDrip x264]')
        title = title.replace('[DVDrip]', '[DVDrip x264]')
        title = title.replace('[DVDRIP-AC3.5.1]', '[DVDrip x264]')
        title = title.replace('[BLuRayRip]', '[720p BlueRay x264]')
        title = title.replace('[BRrip]', '[720p BlueRay x264]')
        title = title.replace('[BDrip]', '[720p BlueRay x264]')
        title = title.replace('[BluRay Rip]', '[720p BlueRay x264]')
        title = title.replace('[BluRay 720p]', '[720p BlueRay x264]')
        title = title.replace('[BluRay 1080p]', '[1080p BlueRay x264]')
        title = title.replace('[BluRay MicroHD]', '[1080p BlueRay x264]')
        title = title.replace('[MicroHD 1080p]', '[1080p BlueRay x264]')

        return title.strip()


class newpctCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # set this 0 to suppress log line, since we aren't updating it anyways
        self.minTime = 0

    def _getRSSData(self):
        return {'entries': []}


provider = newpctProvider()
