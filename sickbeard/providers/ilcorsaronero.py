# coding=utf-8
# Author: m0m4x
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
import traceback
import urllib

from sickbeard import db, logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException

from sickrage.helper.common import convert_size, try_int
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

category_excluded = {'Screener': 19, #shit
                     'Musica': 2,
                     'Audiolibri': 18,
                     'Ebooks': 6,
                     'App Win': 7,
                     'App Linux': 8,
                     'App Mac': 9,
                     'PlayStation': 13,
                     'XBOX': 14,
                     'PC Games': 3,
                     'H4cikn9': 16,
                     'Altro': 4,
                     }

#'BDRiP': 2,
#'Anime': 5,
#'DVD': 20,
#'SerieTv': 15

class ilCorsaroNeroProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "ilCorsaroNero")

        self._uid = None
        self._hash = None
        self.cat = None
        self.engrelease = None
        self.page = 10
        self.subtitle = None
        self.minseed = None
        self.minleech = None

        self.hdtext = [' - Versione 720p',
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
                       ' 720p']

        self.category_dict = {'Serie TV': 15,
                              'BDRip': 1,
                              'DVD': 20,
                              'Anime': 5,
                              'Screener': 19}

        self.urls = {'base_url': 'http://ilcorsaronero.info',
                     'detail': 'http://ilcorsaronero.info/tor/%s/',
                     'search': 'http://ilcorsaronero.info/argh.php?search=%s',
                     'search_page': 'http://ilcorsaronero.info/advsearch.php?search={0}&&order=data&by=DESC&page={1}',
                     'download': 'http://itorrents.org/torrent/%s.torrent'}

        self.url = self.urls['base_url']

        self.sub_string = ['sub', 'softsub']

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll TNTVillage every 30 minutes max

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
        logger.log(u"Episode quality: {0}".format(file_quality), logger.DEBUG)

        def checkName(options, func):
            return func([re.search(option, file_quality, re.I) for option in options])

        dvdOptions = checkName(["dvd", "dvdrip", "dvdmux", "DVD9", "DVD5"], any)
        bluRayOptions = checkName(["BD", "BDmux", "BDrip", "BRrip", "Bluray"], any)
        sdOptions = checkName(["h264", "divx", "XviD", "tv", "TVrip", "SATRip", "DTTrip", "Mpeg2"], any)
        hdOptions = checkName(["720p"], any)
        fullHD = checkName(["1080p", "fullHD"], any)
        webdl = checkName(["webdl", "webmux", "webrip", "dl-webmux", "web-dlmux", "webdl-mux", "web-dl", "webdlmux", "dlmux"], any)

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

            if re.search("ita", name.split(sub)[0], re.I):
                logger.log(u"Found Italian release:  " + name, logger.DEBUG)
                italian = True
                break

        if not subFound and re.search("ita", name, re.I):
            logger.log(u"Found Italian release:  " + name, logger.DEBUG)
            italian = True

        return italian

    @staticmethod
    def _is_english(name):

        if not name or name == 'None':
            return False

        english = False
        if re.search("eng", name, re.I):
            logger.log(u"Found English release:  " + name, logger.DEBUG)
            english = True

        return english

    @staticmethod
    def _is_season_pack(name):

        try:
            parse_result = NameParser(tryIndexers=True).parse(name)
        except (InvalidNameException, InvalidShowException) as error:
            logger.log(u"{0}".format(error), logger.DEBUG)
            return False

        main_db_con = db.DBConnection()
        sql_selection = "select count(*) as count from tv_episodes where showid = ? and season = ?"
        episodes = main_db_con.select(sql_selection, [parse_result.show.indexerid, parse_result.season_number])
        if int(episodes[0][b'count']) == len(parse_result.episode_numbers):
            return True

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                self.page = 1
                last_page = 0
                y = int(self.page)

                if search_string == '':
                    continue

                search_string = str(search_string).replace('.', ' ')

                for x in range(0, y):

                    if last_page:
                        break

                    search_url = (self.urls['search_page']).format(search_string, x)

                    logger.log(u"Search string: {0}".format
                                   (search_string.decode("utf-8")), logger.DEBUG)

                    data = self.get_url(search_url, returns='text')
                    if not data:
                        logger.log(u"No data returned from provider", logger.DEBUG)
                        continue

                    try:
                        with BS4Parser(data, 'html5lib') as html:
                            torrent_table = html.find('tr', class_='bordo').find_parent("table")
                            torrent_rows = torrent_table('tr') if torrent_table else []

                            # Continue only if one Release is found
                            if (len(torrent_rows) < 6) or (len(torrent_rows[2]('td')) == 1):
                                logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                                last_page = 1
                                continue

                            if len(torrent_rows) < 45:
                                last_page = 1

                            for result in torrent_rows[2:-3]:

                                try:
                                    link = result('td')[1].find('a')['href']
                                    title = re.sub(' +',' ', link.rsplit('/', 1)[-1].replace('_', ' '))
                                    hash = result('td')[3].find('input', class_='downarrow')['value'].upper()
                                    leechers = result('td')[6].text
                                    leechers = int(leechers.strip('[]'))
                                    seeders = result('td')[5].text
                                    seeders = int(seeders.strip('[]'))
                                    torrent_size = result('td')[2].string
                                    size = convert_size(torrent_size) or -1

                                    # Download Urls
                                    download_url = self.urls['download'] % hash
                                    if urllib.urlopen(download_url).getcode() == 404:
                                        logger.log(u"Torrent hash not found in itorrents.org, searching for magnet",
                                                   logger.DEBUG)
                                        data_detail = self.get_url(link, returns='text')
                                        with BS4Parser(data_detail, 'html5lib') as html_detail:
                                            sources_row = html_detail.find('td', class_="header2").parent
                                            source_magnet = sources_row('td')[1].find('a', class_='forbtn', title='Magnet')
                                            if source_magnet and not source_magnet == 'None':
                                                download_url = source_magnet['href']
                                            else:
                                                continue

                                except (AttributeError, TypeError):
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
                                    logger.log(u"Torrent is subtitled, skipping: {0} ".format(title), logger.DEBUG)
                                    continue

                                if self.engrelease and not self._is_english(title):
                                    logger.log(u"Torrent isnt english audio/subtitled , skipping: {0} ".format(title), logger.DEBUG)
                                    continue

                                search_show = re.split(r'([Ss][\d{1,2}]+)', search_string)[0]
                                show_title = search_show
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
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                                   (title, seeders, leechers), logger.DEBUG)
                                    continue

                                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                                if mode != 'RSS':
                                    logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                                items.append(item)

                    except Exception:
                        logger.log(u"Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.ERROR)

                # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

                results += items

        return results


provider = ilCorsaroNeroProvider()
