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

import re
from sickbeard.providers import generic
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException, ex

class IPTorrentsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "IPTorrents")

        self.supportsBacklog = True


        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.cache = IPTorrentsCache(self)

        self.urls = {'base_url': 'https://iptorrents.eu',
                     'login': 'https://iptorrents.eu/torrents/',
                     'search': 'https://iptorrents.eu/t?%s%s&q=%s&qf=#torrents'}

        self.url = self.urls['base_url']

        self.categories = '73=&60='

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'login': 'submit'}

        self.getURL(self.urls['login'], timeout=30)
        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('tries left', response):
            logger.log(u"You tried too often, please try again after 1 hour! Disable IPTorrents for at least 1 hour", logger.WARNING)
            return False
        if re.search('Password not correct', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '&free=on' if self.freeleech else ''

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                searchURL = self.urls['search'] % (self.categories, freeleech, search_string)
                searchURL += ';o=seeders' if mode is not 'RSS' else ''
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    data = re.sub(r'(?im)<button.+?<[\/]button>', '', data, 0)
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        if not html:
                            logger.log(u"No data returned from provider", logger.DEBUG)
                            continue

                        if html.find(text='No Torrents Found!'):
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_table = html.find('table', attrs={'class': 'torrents'})
                        torrents = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrents) < 2:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrents[1:]:
                            try:
                                title = result.find_all('td')[1].find('a').text
                                download_url = self.urls['base_url'] + result.find_all('td')[3].find('a')['href']
                                size = self._convertSize(result.find_all('td')[5].text)
                                seeders = int(result.find('td', attrs={'class': 'ac t_seeders'}).text)
                                leechers = int(result.find('td', attrs = {'class' : 'ac t_leechers'}).text)
                            except (AttributeError, TypeError, KeyError):
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
                    logger.log(u"Failed parsing provider. Error: %r" % ex(e), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

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

class IPTorrentsCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll IPTorrents every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = IPTorrentsProvider()
