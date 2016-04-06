# coding=utf-8
# Author: Idan Gutman
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
import traceback
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class HoundDawgsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "HoundDawgs")

        self.username = None
        self.password = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None
        self.ranked = None

        self.urls = {
            'base_url': 'https://hounddawgs.org/',
            'search': 'https://hounddawgs.org/torrents.php',
            'login': 'https://hounddawgs.org/login.php'
        }

        self.url = self.urls['base_url']

        self.search_params = {
            "filter_cat[85]": 1,
            "filter_cat[58]": 1,
            "filter_cat[57]": 1,
            "filter_cat[74]": 1,
            "filter_cat[92]": 1,
            "filter_cat[93]": 1,
            "order_by": "s3",
            "order_way": "desc",
            "type": '',
            "userid": '',
            "searchstr": '',
            "searchimdb": '',
            "searchtags": ''
        }

        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'keeplogged': 'on',
            'login': 'Login'
        }

        self.get_url(self.urls['base_url'], returns='text')
        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Dit brugernavn eller kodeord er forkert.', response) \
                or re.search('<title>Login :: HoundDawgs</title>', response) \
                or re.search('Dine cookies er ikke aktiveret.', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        results = []
        if not self.login():
            return results

        for mode in search_strings:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                self.search_params['searchstr'] = search_string

                data = self.get_url(self.urls['search'], params=self.search_params, returns='text')
                if not data:
                    logger.log(u'URL did not return data', logger.DEBUG)
                    continue

                strTableStart = "<table class=\"torrent_table"
                startTableIndex = data.find(strTableStart)
                trimmedData = data[startTableIndex:]
                if not trimmedData:
                    continue

                try:
                    with BS4Parser(trimmedData, 'html5lib') as html:
                        result_table = html.find('table', {'id': 'torrent_table'})

                        if not result_table:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        result_tbody = result_table.find('tbody')
                        entries = result_tbody.contents
                        del entries[1::2]

                        for result in entries[1:]:

                            torrent = result('td')
                            if len(torrent) <= 1:
                                break

                            allAs = (torrent[1])('a')

                            try:
                                notinternal = result.find('img', src='/static//common/user_upload.png')
                                if self.ranked and notinternal:
                                    logger.log(u"Found a user uploaded release, Ignoring it..", logger.DEBUG)
                                    continue
                                freeleech = result.find('img', src='/static//common/browse/freeleech.png')
                                if self.freeleech and not freeleech:
                                    continue
                                title = allAs[2].string
                                download_url = self.urls['base_url'] + allAs[0].attrs['href']
                                torrent_size = result.find("td", class_="nobr").find_next_sibling("td").string
                                if torrent_size:
                                    size = convert_size(torrent_size) or -1
                                seeders = try_int((result('td')[6]).text)
                                leechers = try_int((result('td')[7]).text)

                            except (AttributeError, TypeError):
                                continue

                            if not title or not download_url:
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
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


provider = HoundDawgsProvider()
