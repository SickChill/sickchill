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

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic

from sickbeard.bs4_parser import BS4Parser

class NextGenProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "NextGen")

        self.supportsBacklog = True


        self.username = None
        self.password = None
        self.ratio = None

        self.cache = NextGenCache(self)

        self.urls = {'base_url': 'https://nxtgn.biz/',
                     'search': 'https://nxtgn.biz/browse.php?search=%s&cat=0&incldead=0&modes=%s',
                     'login_page': 'https://nxtgn.biz/login.php'}

        self.url = self.urls['base_url']

        self.categories = '&c7=1&c24=1&c17=1&c22=1&c42=1&c46=1&c26=1&c28=1&c43=1&c4=1&c31=1&c45=1&c33=1'

        self.last_login_check = None

        self.login_opener = None

        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

    def getLoginParams(self):
        return {
            'username': self.username,
            'password': self.password,
        }

    def loginSuccess(self, output):
        if "<title>NextGen - Login</title>" in output:
            return False
        else:
            return True

    def _doLogin(self):

        now = time.time()
        if self.login_opener and self.last_login_check < (now - 3600):
            try:
                output = self.getURL(self.urls['test'])
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
            login_params = self.getLoginParams()
            data = self.getURL(self.urls['login_page'])
            if not data:
                return False

            with BS4Parser(data) as bs:
                csrfraw = bs.find('form', attrs={'id': 'login'})['action']
                output = self.getURL(self.urls['base_url'] + csrfraw, post_data=login_params)

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

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (urllib.quote(search_string.encode('utf-8')), self.categories)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data.decode('iso-8859-1'), features=["html5lib", "permissive"]) as html:
                        resultsTable = html.find('div', attrs={'id': 'torrent-table-wrapper'})

                        if not resultsTable:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        # Collecting entries
                        entries_std = html.find_all('div', attrs={'id': 'torrent-std'})
                        entries_sticky = html.find_all('div', attrs={'id': 'torrent-sticky'})

                        entries = entries_std + entries_sticky

                        # Xirg STANDARD TORRENTS
                        # Continue only if one Release is found
                        if not entries:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in entries:

                            try:
                                title = result.find('div', attrs={'id': 'torrent-udgivelse2-users'}).a['title']
                                download_url = self.urls['base_url'] + result.find('div', attrs={'id': 'torrent-download'}).a['href']
                                seeders = int(result.find('div', attrs={'id' : 'torrent-seeders'}).text)
                                leechers = int(result.find('div', attrs={'id' : 'torrent-leechers'}).text)
                                size = self._convertSize(result.find('div', attrs={'id' : 'torrent-size'}).text)
                                freeleech = result.find('div', attrs={'id': 'browse-mode-F2L'}) is not None
                            except (AttributeError, TypeError, KeyError):
                                continue

                            if self.freeleech and not freeleech:
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode is not 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _convertSize(self, size):
        size, modifier = size[:-2], size[-2:]
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

    def seedRatio(self):
        return self.ratio


class NextGenCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll NextGen every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = NextGenProvider()
