# coding=utf-8
# Author: CristianBB
# Greetings to Mr. Pine-apple
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

from __future__ import unicode_literals
from requests.compat import urljoin
import re

from sickbeard import helpers
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class newpctProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, 'Newpct')

        self.onlyspasearch = None

        self.url = 'http://www.newpct.com'
        self.urls = {'search': urljoin(self.url, 'index.php')}

        self.cache = tvcache.TVCache(self, min_time=20)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        """
        Search query:
        http://www.newpct.com/index.php?l=doSearch&q=fringe&category_=All&idioma_=1&bus_de_=All

        q => Show name
        category_ = Category 'Shows' (767)
        idioma_ = Language Spanish (1)
        bus_de_ = Date from (All, hoy)

        """
        results = []

        # Only search if user conditions are true
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        search_params = {
            'l': 'doSearch',
            'q': '',
            'category_': 'All',
            'idioma_': 1,
            'bus_de_': 'All'
        }

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                logger.log('Show info is not spanish, skipping provider search', logger.DEBUG)
                continue

            search_params['bus_de_'] = 'All' if mode != 'RSS' else 'hoy'

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log('Search string: {0}'.format
                               (search_string.decode('utf-8')), logger.DEBUG)

                search_params['q'] = search_string

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('table', id='categoryTable')
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 3:  # Headers + 1 Torrent + Pagination
                        logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                        continue

                    # 'Fecha', 'Título', 'Tamaño', ''
                    # Date, Title, Size
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]('th')]
                    for row in torrent_rows[1:-1]:
                        try:
                            cells = row('td')

                            torrent_row = row.find('a')
                            title = self._processTitle(torrent_row.get('title', ''))
                            download_url = torrent_row.get('href', '')
                            if not all([title, download_url]):
                                continue

                            # Provider does not provide seeders/leechers
                            seeders = 1
                            leechers = 0
                            torrent_size = cells[labels.index('Tamaño')].get_text(strip=True)

                            size = convert_size(torrent_size) or -1
                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}
                            if mode != 'RSS':
                                logger.log('Found result: {0}'.format(title), logger.DEBUG)

                            items.append(item)
                        except (AttributeError, TypeError):
                            continue

            results += items

        return results

    def get_url(self, url, post_data=None, params=None, timeout=30, **kwargs):  # pylint: disable=too-many-arguments
        """
        returns='content' when trying access to torrent info (For calling torrent client). Previously we must parse
        the URL to get torrent file
        """
        trickery = kwargs.pop('returns', '')
        if trickery == 'content':
            kwargs['returns'] = 'text'
            data = super(newpctProvider, self).get_url(url, post_data=post_data, params=params, timeout=timeout, **kwargs)
            url = re.search(r'http://tumejorserie.com/descargar/.+\.torrent', data, re.DOTALL).group()
            url = urljoin(self.url, url.rsplit('=', 1)[-1])

        kwargs['returns'] = trickery
        return super(newpctProvider, self).get_url(url, post_data=post_data, params=params,
                                                   timeout=timeout, **kwargs)

    def download_result(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self.login():
            return False

        urls, filename = self._make_url(result)

        for url in urls:
            # Search results don't return torrent files directly, it returns show sheets so we must parse showSheet to access torrent.
            data = self.get_url(url, returns='text')
            url_torrent = re.search(r'http://tumejorserie.com/descargar/.+\.torrent', data, re.DOTALL).group()

            if url_torrent.startswith('http'):
                self.headers.update({'Referer': '/'.join(url_torrent.split('/')[:3]) + '/'})

            logger.log('Downloading a result from {0}'.format(url))

            if helpers.download_file(url_torrent, filename, session=self.session, headers=self.headers):
                if self._verify_download(filename):
                    logger.log('Saved result to {0}'.format(filename), logger.INFO)
                    return True
                else:
                    logger.log('Could not download {0}'.format(url), logger.WARNING)
                    helpers.remove_file_failed(filename)

        if urls:
            logger.log('Failed to download any results', logger.WARNING)

        return False

    @staticmethod
    def _processTitle(title):
        # Remove 'Mas informacion sobre ' literal from title
        title = title[22:]

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV 1080p[^\[]*]', '1080p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV 720p[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[ALTA DEFINICION 720p[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV]', 'HDTV x264', title, flags=re.I)
        title = re.sub(r'\[DVD[^\[]*]', 'DVDrip x264', title, flags=re.I)
        title = re.sub(r'\[BluRay 1080p[^\[]*]', '1080p BlueRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay MicroHD[^\[]*]', '1080p BlueRay x264', title, flags=re.I)
        title = re.sub(r'\[MicroHD 1080p[^\[]*]', '1080p BlueRay x264', title, flags=re.I)
        title = re.sub(r'\[BLuRay[^\[]*]', '720p BlueRay x264', title, flags=re.I)
        title = re.sub(r'\[BRrip[^\[]*]', '720p BlueRay x264', title, flags=re.I)
        title = re.sub(r'\[BDrip[^\[]*]', '720p BlueRay x264', title, flags=re.I)

        # Language
        title = re.sub(r'\[Spanish[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(r'\[Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(ur'\[Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(ur'\[AC3 5\.1 Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)

        title += '-NEWPCT'

        return title.strip()

provider = newpctProvider()
