# coding=utf-8
# Author: m0m4x
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

import six
from requests.compat import quote_plus, urljoin

from sickbeard import db, logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class ilCorsaroNeroProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):
        TorrentProvider.__init__(self, 'ilCorsaroNero')

        categories = [  # Categories included in searches
            15,  # Serie TV
            5,  # Anime
            1,  # BDRip
            20,  # DVD
            19,  # Screener
        ]
        categories = ','.join(map(six.text_type, categories))

        self.url = 'https://ilcorsaronero.info'
        self.urls = {
            'search': urljoin(self.url, 'advsearch.php?search={0}&order=data&by=DESC&page={1}&category=' + categories),
        }

        self.public = True
        self.minseed = None
        self.minleech = None

        self.engrelease = None
        self.subtitle = None
        self.max_pages = 10

        self.proper_strings = ['PROPER', 'REPACK']
        self.sub_string = ['sub', 'softsub']

        self.hdtext = [
            ' - Versione 720p',
            ' Versione 720p',
            ' V 720p',
            ' V 720',
            ' V HEVC',
            ' V  HEVC',
            ' V 1080',
            ' Versione 1080p',
            ' 720p HEVC',
            ' Ver 720',
            ' 720p HEVC',
            ' 720p',
        ]

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ilCorsaroNero every 30 minutes max

    @staticmethod
    def _reverseQuality(quality):

        quality_string = ''

        if quality == Quality.SDTV:
            quality_string = ' HDTV x264'
        if quality == Quality.SDDVD:
            quality_string = ' DVDRIP'
        elif quality == Quality.HDTV:
            quality_string = ' 720p HDTV x264'
        elif quality == Quality.FULLHDTV:
            quality_string = ' 1080p HDTV x264'
        elif quality == Quality.RAWHDTV:
            quality_string = ' 1080i HDTV mpeg2'
        elif quality == Quality.HDWEBDL:
            quality_string = ' 720p WEB-DL h264'
        elif quality == Quality.FULLHDWEBDL:
            quality_string = ' 1080p WEB-DL h264'
        elif quality == Quality.HDBLURAY:
            quality_string = ' 720p Bluray x264'
        elif quality == Quality.FULLHDBLURAY:
            quality_string = ' 1080p Bluray x264'

        return quality_string

    @staticmethod
    def _episodeQuality(torrent_rows):  # pylint: disable=too-many-return-statements, too-many-branches
        """
            Return The quality from the scene episode HTML row.
        """

        file_quality = (torrent_rows('td'))[1].find('a')['href'].replace('_', ' ')
        logger.log(u'Episode quality: {0}'.format(file_quality), logger.DEBUG)

        def checkName(options, func):
            return func([re.search(option, file_quality, re.I) for option in options])

        dvdOptions = checkName(['dvd', 'dvdrip', 'dvdmux', 'DVD9', 'DVD5'], any)
        bluRayOptions = checkName(['BD', 'BDmux', 'BDrip', 'BRrip', 'Bluray'], any)
        sdOptions = checkName(['h264', 'divx', 'XviD', 'tv', 'TVrip', 'SATRip', 'DTTrip', 'Mpeg2'], any)
        hdOptions = checkName(['720p'], any)
        fullHD = checkName(['1080p', 'fullHD'], any)
        webdl = checkName(['webdl', 'webmux', 'webrip', 'dl-webmux', 'web-dlmux', 'webdl-mux', 'web-dl', 'webdlmux', 'dlmux'], any)

        if sdOptions and not dvdOptions and not fullHD and not hdOptions:
            return Quality.SDTV
        elif dvdOptions:
            return Quality.SDDVD
        elif hdOptions and not bluRayOptions and not fullHD and not webdl:
            return Quality.HDTV
        elif not hdOptions and not bluRayOptions and fullHD and not webdl:
            return Quality.FULLHDTV
        elif hdOptions and not bluRayOptions and not fullHD and webdl:
            return Quality.HDWEBDL
        elif not hdOptions and not bluRayOptions and fullHD and webdl:
            return Quality.FULLHDWEBDL
        elif bluRayOptions and hdOptions and not fullHD:
            return Quality.HDBLURAY
        elif bluRayOptions and fullHD and not hdOptions:
            return Quality.FULLHDBLURAY
        else:
            return Quality.UNKNOWN

    def _is_italian(self, name):

        if not name or name == 'None':
            return False

        subFound = italian = False
        for sub in self.sub_string:
            if re.search(sub, name, re.I):
                subFound = True
            else:
                continue

            if re.search('ita', name.split(sub)[0], re.I):
                logger.log(u'Found Italian release: ' + name, logger.DEBUG)
                italian = True
                break

        if not subFound and re.search('ita', name, re.I):
            logger.log(u'Found Italian release: ' + name, logger.DEBUG)
            italian = True

        return italian

    @staticmethod
    def _is_english(name):

        if not name or name == 'None':
            return False

        english = False
        if re.search('eng', name, re.I):
            logger.log(u'Found English release: ' + name, logger.DEBUG)
            english = True

        return english

    @staticmethod
    def _is_season_pack(name):

        try:
            parse_result = NameParser(tryIndexers=True).parse(name)
        except (InvalidNameException, InvalidShowException) as error:
            logger.log(u'{0}'.format(error), logger.DEBUG)
            return False

        main_db_con = db.DBConnection()
        sql_selection = 'select count(*) as count from tv_episodes where showid = ? and season = ?'
        episodes = main_db_con.select(sql_selection, [parse_result.show.indexerid, parse_result.season_number])
        if int(episodes[0][b'count']) == len(parse_result.episode_numbers):
            return True

    @staticmethod
    def _magnet_from_result(info_hash, title):
        return 'magnet:?xt=urn:btih:{hash}&dn={title}&tr={trackers}'.format(
            hash=info_hash,
            title=quote_plus(title),
            trackers='http://tracker.tntvillage.scambioetico.org:2710/announce')

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []

        for mode in search_params:
            items = []
            logger.log(u'Search Mode: {0}'.format(mode), logger.DEBUG)
            for search_string in search_params[mode]:
                if search_string == '':
                    continue

                search_string = six.text_type(search_string).replace('.', ' ')
                logger.log(u'Search string: {0}'.format(search_string.decode('utf-8')), logger.DEBUG)

                last_page = False
                for page in range(0, self.max_pages):
                    if last_page:
                        break

                    logger.log('Processing page {0} of results'.format(page), logger.DEBUG)
                    search_url = self.urls['search'].format(search_string, page)

                    data = self.get_url(search_url, returns='text')
                    if not data:
                        logger.log(u'No data returned from provider', logger.DEBUG)
                        continue

                    try:
                        with BS4Parser(data, 'html5lib') as html:
                            table_header = html.find('tr', class_='bordo')
                            torrent_table = table_header.find_parent('table') if table_header else None
                            if not torrent_table:
                                logger.log(u'Could not find table of torrents', logger.ERROR)
                                continue

                            torrent_rows = torrent_table('tr')

                            # Continue only if one Release is found
                            if len(torrent_rows) < 6 or len(torrent_rows[2]('td')) == 1:
                                logger.log(u'Data returned from provider does not contain any torrents', logger.DEBUG)
                                last_page = True
                                continue

                            if len(torrent_rows) < 45:
                                last_page = True

                            for result in torrent_rows[2:-3]:
                                result_cols = result('td')
                                if len(result_cols) == 1:
                                    # Ignore empty rows in the middle of the table
                                    continue
                                try:
                                    info_link = result('td')[1].find('a')['href']
                                    title = re.sub(' +', ' ', info_link.rsplit('/', 1)[-1].replace('_', ' '))
                                    info_hash = result('td')[3].find('input', class_='downarrow')['value'].upper()
                                    download_url = self._magnet_from_result(info_hash, title)
                                    seeders = try_int(result('td')[5].text)
                                    leechers = try_int(result('td')[6].text)
                                    torrent_size = result('td')[2].string
                                    size = convert_size(torrent_size) or -1

                                except (AttributeError, IndexError, TypeError):
                                    continue

                                filename_qt = self._reverseQuality(self._episodeQuality(result))
                                for text in self.hdtext:
                                    title1 = title
                                    title = title.replace(text, filename_qt)
                                    if title != title1:
                                        break

                                if Quality.nameQuality(title) == Quality.UNKNOWN:
                                    title += filename_qt

                                if not self._is_italian(title) and not self.subtitle:
                                    logger.log(u'Torrent is subtitled, skipping: {0}'.format(title), logger.DEBUG)
                                    continue

                                if self.engrelease and not self._is_english(title):
                                    logger.log(u'Torrent isn\'t english audio/subtitled, skipping: {0}'.format(title),
                                               logger.DEBUG)
                                    continue

                                search_show = re.split(r'([Ss][\d{1,2}]+)', search_string)[0]
                                show_title = search_show
                                ep_params = ''
                                rindex = re.search(r'([Ss][\d{1,2}]+)', title)
                                if rindex:
                                    show_title = title[:rindex.start()]
                                    ep_params = title[rindex.start():]
                                if show_title.lower() != search_show.lower() and search_show.lower() in show_title.lower():
                                    new_title = search_show + ep_params
                                    title = new_title

                                if not all([title, download_url]):
                                    continue

                                if self._is_season_pack(title):
                                    title = re.sub(r'([Ee][\d{1,2}\-?]+)', '', title)

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    logger.log(u'Discarding torrent because it doesn\'t meet the minimum'
                                               u' seeders or leechers: {0} (S:{1} L:{2})'.format(
                                        title, seeders, leechers), logger.DEBUG)
                                    continue

                                item = {'title': title, 'link': download_url, 'size': size,
                                        'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                                if mode != 'RSS':
                                    logger.log(u'Found result: {0} with {1} seeders and {2} leechers'.format(
                                        title, seeders, leechers), logger.DEBUG)

                                items.append(item)

                    except Exception as error:
                        logger.log(u'Failed parsing provider. Error: {0}'.format(error), logger.ERROR)

                # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

                results += items

        return results


provider = ilCorsaroNeroProvider()
