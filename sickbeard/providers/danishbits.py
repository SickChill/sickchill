# coding=utf-8
# Author: seedboy
# URL: https://github.com/seedboy
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import urllib
import time
import re

from sickbeard import logger
from sickbeard import tvcache
from sickrage.providers.TorrentProvider import TorrentProvider

from sickbeard.bs4_parser import BS4Parser


class DanishbitsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "Danishbits")

        self.username = None
        self.password = None
        self.ratio = None

        self.cache = DanishbitsCache(self)

        self.urls = {'base_url': 'https://danishbits.org/',
                     'search': 'https://danishbits.org/torrents.php?action=newbrowse&search=%s%s',
                     'login_page': 'https://danishbits.org/login.php'}

        self.url = self.urls['base_url']

        self.categories = '&group=3'

        self.last_login_check = None

        self.login_opener = None

        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

    @staticmethod
    def loginSuccess(output):
        if not output or "<title>Login :: Danishbits.org</title>" in output:
            return False
        else:
            return True

    def login(self):

        now = time.time()
        if self.login_opener and self.last_login_check < (now - 3600):
            try:
                output = self.get_url(self.urls['test'])
                if self.loginSuccess(output):
                    self.last_login_check = now
                    return True
                else:
                    self.login_opener = None
            except Exception:
                self.login_opener = None

        if self.login_opener:
            return True

        try:
            data = self.get_url(self.urls['login_page'])
            if not data:
                return False

            login_params = {
                'username': self.username,
                'password': self.password,
            }
            output = self.get_url(self.urls['login_page'], post_data=login_params)
            if self.loginSuccess(output):
                self.last_login_check = now
                self.login_opener = self.session
                return True

            error = 'unknown'
        except Exception:
            error = traceback.format_exc()
            self.login_opener = None

        self.login_opener = None
        logger.log(u"Failed to login: %s" % error, logger.ERROR)
        return False

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches,too-many-locals

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self.login():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:
                if mode == 'RSS':
                    continue

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (urllib.quote(search_string.encode('utf-8')), self.categories)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.get_url(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data.decode('iso-8859-1'), features=["html5lib", "permissive"]) as html:
                        # Collecting entries
                        entries = html.find_all('tr', attrs={'class': 'torrent'})

                        # Xirg STANDARD TORRENTS
                        # Continue only if one Release is found
                        if not entries:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in entries:

                            # try:
                            title = result.find('div', attrs={'class': 'croptorrenttext'}).find('b').text
                            download_url = self.urls['base_url'] + result.find('span', attrs={'class': 'right'}).find('a')['href']
                            seeders = int(result.find_all('td')[6].text)
                            leechers = int(result.find_all('td')[7].text)
                            size = self._convertSize(result.find_all('td')[2].text)
                            freeleech = result.find('span', class_='freeleech')
                            # except (AttributeError, TypeError, KeyError):
                            #     logger.log(u"attrErr: {0}, tErr: {1}, kErr: {2}".format(AttributeError, TypeError, KeyError), logger.DEBUG)
                            #    continue

                            if self.freeleech and not freeleech:
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
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    @staticmethod
    def _convertSize(size):
        regex = re.compile(r'(.+?\w{2})\d+ file\w')
        m = regex.match(size)
        size = m.group(1)

        size, modifier = size[:-2], size[-2:]
        size = size.replace(',', '')  # strip commas from comma separated values

        size = float(size)
        if modifier in 'KB':
            size *= 1024 ** 1
        elif modifier in 'MB':
            size *= 1024 ** 2
        elif modifier in 'GB':
            size *= 1024 ** 3
        elif modifier in 'TB':
            size *= 1024 ** 4
        return long(size)

    def seedRatio(self):
        return self.ratio


class DanishbitsCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll Danishbits every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}


provider = DanishbitsProvider()
