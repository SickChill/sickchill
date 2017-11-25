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

from __future__ import print_function, unicode_literals

import re

from requests.compat import urljoin

from sickbeard import helpers, logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size
from sickbeard.show_name_helpers import allPossibleShowNames
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class newpctProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, 'Newpct')

        self.onlyspasearch = None

        self.url = 'http://www.newpct.com'
        self.urls = {'search': [ urljoin(self.url, '/series'),
                                 urljoin(self.url, '/series-hd')],
                                 #urljoin(self.url, '/series-vo')],
                     'rss':urljoin(self.url, '/feed'),
                     'download': 'http://tumejorserie.com/descargar/index.php?link=torrents/%s.torrent',}

        self.cache = tvcache.TVCache(self, min_time=20)

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}

        for show_name in set(allPossibleShowNames(ep_obj.show)):
            search_string['Season'].append(show_name)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        search_string = {'Episode': []}

        for show_name in set(allPossibleShowNames(ep_obj.show)):
            search_string['Episode'].append(show_name)

        return [search_string]

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals

        results = []

        # Only search if user conditions are true
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            if mode == 'RSS':

                data = self.cache.get_rss_feed(self.urls['rss'], params=None)['entries']
                if not data:
                    logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                    continue

                for curItem in data:
                    try:

                        title = curItem['title'].decode('utf8')
                        download_url = curItem['link']
                        if not all([title, download_url]):
                            continue

                        title = self._processTitle(title, None, download_url)
                        result = {'title': title, 'link': download_url}

                        items.append(result)
                    except StandardError:
                        continue

            else:

                # Only search if user conditions are true
                if self.onlyspasearch and lang_info != 'es':
                    logger.log('Show info is not spanish, skipping provider search', logger.DEBUG)
                    continue

                for series_name in search_strings[mode]:
                    search_name = re.sub(r'[ \.\(\)]', '-', series_name, flags=re.I)
                    search_names = [search_name]
                    search_name = re.sub(r'-+', '-', search_name, flags=re.I)
                    if not search_name in search_names:
                        search_names.append(search_name)

                    for search_name in search_names:
                        for search_url in self.urls['search']:
                            pg = 1
                            while True:
                                url = search_url + '/' + search_name + '//pg/' + str(pg)

                                try:
                                    data = self.get_url(url, params=None, returns='text')
                                    items = self.parse(series_name, data, mode)
                                    if not len(items):
                                        break
                                    results += items
                                except Exception:
                                    logger.log('No data returned from provider', logger.DEBUG)
                                    break

                                pg += 1

            results += items

        return results

    def parse(self, series_name, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """

        results = []

        with BS4Parser(data) as html:
            torrent_table = html.find('ul', class_='buscar-list')
            torrent_rows = torrent_table('li') if torrent_table else []

            # Continue only if at least one release is found
            if not len(torrent_rows):
                sickrage.app.srLogger.debug('Data returned from provider does not contain any torrents')
                return results

            for row in torrent_rows:
                try:
                    torrent_anchor = row.find_all('a')[1]
                    title = torrent_anchor.get_text()
                    download_url = torrent_anchor.get('href', '')

                    if not all([title, download_url]):
                        continue

                    row_spans = row.find_all('span')
                    size = convert_size(row_spans[-2].get_text().strip()) if row_spans and len(row_spans) >= 2 else 0
                    seeders = 1  # Provider does not provide seeders
                    leechers = 0  # Provider does not provide leechers

                    title = self._processTitle(title, series_name, download_url)

                    logger.log('Found: {0} # Size {1}'.format(title, size), logger.DEBUG)

                    item = {
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers,
                    }

                    results.append(item)

                except (AttributeError, TypeError):
                    continue

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

            match = re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', data, re.DOTALL)
            if not match:
                return None
            
            download_id = match.group(1)
            url = self.urls['download'] % download_id

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

            download_id = re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', data, re.DOTALL).group(1)
            url_torrent = self.urls['download'] % download_id

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

    def _processTitle(self, title, series_name, url, try_download = True):

        # Newpct titles are very very very inconsistent.

        # Check if title is well formatted (RSS titles usually are)
        # Examples:
        # FooSeries - Temporada 2 [HDTV 720p][Cap.204][AC3 5.1 EspaÃ±ol Castellano]
        # Salvation - Temporada 1 [HDTV][Cap.104-107][EspaÃ±ol Castellano]

        # else try to match list format
        # example
        # Serie Juego De Tronos  Temporada 7 Capitulo 5 - Español Castellano Calidad [ HDTV ]
        # Serie Juego De Tronos  Temporada [7] Capitulo [5] - Español Castellano Calidad [ HDTV ]

        # else process download page title
        # else compose from download url

        series_name = series_name or ""

        logger.log('newpct _processTitle: {} # series_name {} # url {}'.format(title, series_name, url), logger.DEBUG)

        #clean spaces
        title = self._clean_spaces(title)
        series_name = self._clean_spaces(series_name)

        title_stdformat = r'.+-.+\d{1,2}.+\[Cap.\d{2,4}([\-\_]\d{2,4})?\]'
        title_listformat = r'Serie ?(.+?) ?-? ?Temporada ?\[?(\d+)\]?.*Capitulos? ?\[?(\d+)\]? ?(al ?\[?(\d+)\]?)?.*- ?(.*) ?Calidad ?(.+)'
        title_urlformat = r'.*\/(.*)\/capitulo-(\d{2,4})\/'

        title_is_proper = re.search(r'\b(proper|repack)', title, flags=re.I)

        stdformat_match = re.search(title_stdformat, title, flags=re.I)
        if not stdformat_match:
            #Try to match list format
            listformat_match = re.search(title_listformat, title, flags=re.I)
            if listformat_match:
                if series_name:
                    name = series_name + ((' (' + title_is_proper.group() + ')') if title_is_proper else "")
                else:
                    name = self._clean_spaces(listformat_match.group(1))
                season = self._clean_spaces(listformat_match.group(2))
                episode = self._clean_spaces(listformat_match.group(3)).zfill(2)
                audioquality = self._clean_spaces(listformat_match.group(6))
                quality = self._clean_spaces(listformat_match.group(7))

                if not listformat_match.group(5):
                    title = "{0} - Temporada {1} {2} [Cap.{3}{4}]".format(name, season, quality, season, episode)
                else:
                    episode_to = self._clean_spaces(listformat_match.group(5)).zfill(2)
                    title = "{0} - Temporada {1} {2} [Cap.{3}{4}_{5}{6}]".format(name, season, quality, season, episode, season, episode_to)
                logger.log('_processTitle: Matched by listFormat: {}'.format(title), logger.DEBUG)
            else:
                if try_download:
                    # Get title from the download page
                    try:
                        data = self.get_url(url, params=None, returns='text')
                        with BS4Parser(data) as details:
                            title = details.find('h1').get_text().split('/')[1]
                            logger.log('_processTitle: Title got from details page: {}'.format(title), logger.DEBUG)
                            return self._processTitle(title, series_name, url, False)
                    except (AttributeError, TypeError):
                        logger.error('title could not be retrived')
                else:
                    # Try to compose title from url
                    url_match = re.search(title_urlformat, url, flags=re.I)
                    if url_match:
                        name = series_name if series_name else url_match.group(1).replace('-', ' ')
                        season, episode = self._process_season_episode(url_match.group(2))
                        title = '{} - Temporada {} [][Cap.{}{}]'.format(name, season, season, episode)
                        logger.log('_processTitle: Matched by url: {}'.format(title), logger.DEBUG)
        else:
            logger.log('_processTitle: Matched by stdFormat: {}'.format(title), logger.DEBUG)

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV 1080p?[^\[]*]', '1080p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV 720p?[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[ALTA DEFINICION 720p?[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV]', 'HDTV x264', title, flags=re.I)
        title = re.sub(r'\[DVD[^\[]*]', 'DVDrip x264', title, flags=re.I)
        title = re.sub(r'\[BluRay 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay Rip 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay Rip 720p?[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay MicroHD[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[MicroHD 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BLuRay[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BRrip[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BDrip[^\[]*]', '720p BluRay x264', title, flags=re.I)

        #detect hdtv/bluray by url
        #hdtv 1080p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-610/hdtv-1080p-ac3-5-1/
        #hdtv 720p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-26/hdtv-720p-ac3-5-1/
        #hdtv example url: http://www.newpct.com/descargar-serie/foo/capitulo-214/hdtv/
        #bluray compilation example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-11/bluray-1080p/
        title_hdtv = re.search(r'HDTV', title, flags=re.I)
        title_720p = re.search(r'720p', title, flags=re.I)
        title_1080p = re.search(r'1080p', title, flags=re.I)
        title_x264 = re.search(r'x264', title, flags=re.I)
        title_bluray = re.search(r'bluray', title, flags=re.I)
        title_vo = re.search(r'\[V.O.[^\[]*]', title, flags=re.I)
        url_hdtv = re.search(r'HDTV', url, flags=re.I)
        url_720p = re.search(r'720p', url, flags=re.I)
        url_1080p = re.search(r'1080p', url, flags=re.I)
        url_bluray = re.search(r'bluray', url, flags=re.I)
        url_serie_hd = re.search(r'descargar\-seriehd', url, flags=re.I)
        url_serie_vo = re.search(r'descargar\-serievo', url, flags=re.I)

        if not title_hdtv and url_hdtv:
            title += ' HDTV'
            if not title_x264:
                title += ' x264'
        if not title_bluray and url_bluray:
            title += ' BluRay'
            if not title_x264:
                title += ' x264'
        if not title_1080p and url_1080p:
            title += ' 1080p'
            title_1080p = True
        if not title_720p and url_720p:
            title += ' 720p'
            title_720p = True
        if not (title_720p or title_1080p) and url_serie_hd:
            title += ' 720p'
        if not (title_vo) and url_serie_vo:
            title += ' [V.O.]'
            title_vo = True

        # Language
        # title = re.sub(r'\[Spanish[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(r'\[Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(ur'\[Espa\u00f1ol[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(ur'\[Espa\u00f1ol Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(r'\[AC3 5\.1[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(ur'\[AC3 5\.1 Espa\u00f1ol[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        # title = re.sub(ur'\[AC3 5\.1 Espa\u00f1ol Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)

        if title_vo:
            title += ' -NEWPCTVO'
        else:
            title += ' -SPANISH AUDIO'
            title += ' -NEWPCT'

        #propers handling
        title = re.sub(r'\(?proper\)?', '-PROPER', title, flags=re.I)
        title = re.sub(r'\(?repack\)?', '-REPACK', title, flags=re.I)

        return self._clean_spaces(title)

    def _process_season_episode(self, season_episode):

        match = re.search(r'(\d)(\d{1,2})', season_episode, flags=re.I)
        if not match:
            match = re.search(r'(\d{2})(\d{2})', season_episode, flags=re.I)

        season = match.group(1)
        episode = match.group(2).zfill(2)

        return season, episode

    def _clean_spaces(self, value):

        value = value.strip()
        value = re.sub(r'[ ]+', ' ', value, flags=re.I)
        value = re.sub(r'\[[ ]+', '[', value, flags=re.I)
        value = re.sub(r'[ ]+\]', ']', value, flags=re.I)
        value = re.sub(r'\([ ]+', '(', value, flags=re.I)
        value = re.sub(r'[ ]+\)', ')', value, flags=re.I)

        return value

provider = newpctProvider()
