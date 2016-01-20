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

import re
from six.moves import urllib
import traceback

from sickbeard import helpers
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class newpctProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Newpct")

        self.onlyspasearch = None
        self.cache = tvcache.TVCache(self, min_time=10)

        # Unsupported
        # self.minseed = None
        # self.minleech = None

        self.urls = {
            'base_url': 'http://www.newpct.com',
            'search': 'http://www.newpct.com/index.php'
        }

        self.url = self.urls['base_url']

        """
        Search query:
        http://www.newpct.com/index.php?l=doSearch&q=fringe&category_=All&idioma_=1&bus_de_=All

        q => Show name
        category_ = Category "Shows" (767)
        idioma_ = Language Spanish (1)
        bus_de_ = Date from (All, hoy)

        """

        self.search_params = {
            'l': 'doSearch',
            'q': '',
            'category_': 'All',
            'idioma_': 1,
            'bus_de_': 'All'
        }

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals

        results = []

        # Only search if user conditions are true
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
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params['q'] = search_string.strip() if mode != 'RSS' else ''
                self.search_params['bus_de_'] = 'All' if mode != 'RSS' else 'hoy'

                search_url = self.urls['search'] + '?' + urllib.parse.urlencode(self.search_params)
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url, timeout=30)
                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_tbody = html.find('tbody')

                        if torrent_tbody is None:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_table = torrent_tbody.findAll('tr')
                        if not len(torrent_table):
                            logger.log(u"Torrent table does not have any rows", logger.DEBUG)
                            continue

                        for row in torrent_table[:-1]:
                            try:
                                torrent_row = row.findAll('a')[0]

                                download_url = torrent_row.get('href', '')

                                title = self._processTitle(torrent_row.get('title', ''))

                                # Provider does not provide seeders/leechers
                                seeders = 1
                                leechers = 0
                                torrent_size = row.findAll('td')[2].text

                                size = convert_size(torrent_size) or -1
                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent (Unsupported)
                            # if seeders < self.minseed or leechers < self.minleech:
                            #     if mode != 'RSS':
                            #         logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            #     continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items.append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            # For each search mode sort all the items by seeders if available (Unsupported)
            # items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def get_url(self, url, post_data=None, params=None, timeout=30, json=False, need_bytes=False):  # pylint: disable=too-many-arguments
        """
        need_bytes=True when trying access to torrent info (For calling torrent client). Previously we must parse
        the URL to get torrent file
        """
        if need_bytes:
            data = helpers.getURL(url, post_data=None, params=None, headers=self.headers, timeout=timeout,
                                  session=self.session, json=json, need_bytes=False)
            url = re.search(r'http://tumejorserie.com/descargar/.+\.torrent', data, re.DOTALL).group()

        return helpers.getURL(url, post_data=post_data, params=params, headers=self.headers, timeout=timeout,
                              session=self.session, json=json, need_bytes=need_bytes)

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
            data = self.get_url(url)
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
    def _processTitle(title):
        # Remove "Mas informacion sobre " literal from title
        title = title[22:]

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV 1080p[^\[]*]', '1080p HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[HDTV 720p[^\[]*]', '720p HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[ALTA DEFINICION 720p[^\[]*]', '720p HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[HDTV]', 'HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[DVD[^\[]*]', 'DVDrip x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[BluRay 1080p[^\[]*]', '1080p BlueRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[BluRay MicroHD[^\[]*]', '1080p BlueRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[MicroHD 1080p[^\[]*]', '1080p BlueRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[BLuRay[^\[]*]', '720p BlueRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[BRrip[^\[]*]', '720p BlueRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[BDrip[^\[]*]', '720p BlueRay x264', title, flags=re.IGNORECASE)

        # Language
        title = re.sub(r'\[Spanish[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)
        title = re.sub(r'\[Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)
        title = re.sub(ur'\[Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)
        title = re.sub(ur'\[AC3 5\.1 Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)

        title += '-NEWPCT'

        return title.strip()

provider = newpctProvider()
