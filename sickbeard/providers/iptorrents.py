# coding=utf-8
# Author: seedboy
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
from requests.utils import dict_from_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser

from sickrage.helper.exceptions import AuthException, ex
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class IPTorrentsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "IPTorrents")

        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll IPTorrents every 10 minutes max

        self.urls = {'base_url': 'https://iptorrents.eu',
                     'login': 'https://iptorrents.eu/torrents/',
                     'search': 'https://iptorrents.eu/t?%s%s&q=%s&qf=#torrents'}

        self.url = self.urls['base_url']

        self.categories = '73=&60='

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'login': 'submit'}

        self.get_url(self.urls['login'], timeout=30)
        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        # Invalid username and password combination
        if re.search('Invalid username and password combination', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        # You tried too often, please try again after 2 hours!
        if re.search('You tried too often', response):
            logger.log(u"You tried too often, please try again after 2 hours! Disable IPTorrents for at least 2 hours", logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        if not self.login():
            return results

        freeleech = '&free=on' if self.freeleech else ''

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {search}".format(search=search_string.decode('utf-8')),
                               logger.DEBUG)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                search_url = self.urls['search'] % (self.categories, freeleech, search_string)
                search_url += ';o=seeders' if mode != 'RSS' else ''
                logger.log(u"Search URL: %s" % search_url, logger.DEBUG)

                data = self.get_url(search_url)
                if not data:
                    continue

                try:
                    data = re.sub(r'(?im)<button.+?<[\/]button>', '', data, 0)
                    with BS4Parser(data, 'html5lib') as html:
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
                                seeders = int(result.find('td', attrs={'class': 'ac t_seeders'}).text)
                                leechers = int(result.find('td', attrs={'class': 'ac t_leechers'}).text)
                                torrent_size = result.find_all('td')[5].text
                                size = convert_size(torrent_size) or -1
                            except (AttributeError, TypeError, KeyError):
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
                                logger.log(u"Found result: %s with %s seeders and %s leechers" % (title, seeders, leechers), logger.DEBUG)

                            items.append(item)

                except Exception as e:
                    logger.log(u"Failed parsing provider. Error: %r" % ex(e), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = IPTorrentsProvider()
