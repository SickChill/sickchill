# coding=utf-8
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import datetime
import traceback

from . import generic
from sickbeard import logger, tvcache, helpers
from sickbeard.bs4_parser import BS4Parser
from lib.unidecode import unidecode


class FunFileProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, 'FunFile')

        self.url_base = 'https://www.funfile.org/'
        self.urls = {'config_provider_home_uri': self.url_base,
                     'login': self.url_base + 'takelogin.php',
                     'search': self.url_base + 'browse.php?%ssearch=%s',
                     'get': self.url_base + '%s'}

        self.categories = 'cat=7&incldead=0&s_title=1&showspam=1&'

        self.url = self.urls['config_provider_home_uri']
        self.url_timeout = 90
        self.username, self.password, self.minseed, self.minleech = 4 * [None]
        self.cache = FunFileCache(self)

    def _do_login(self):

        logged_in = lambda: None is not self.session.cookies.get('uid', domain='.funfile.org') and None is not self.session.cookies.get('pass', domain='.funfile.org')
        if logged_in():
            return True

        if self._check_auth():
            login_params = {'username': self.username, 'password': self.password, 'submit': 'Log in'}
            response = helpers.getURL(self.urls['login'], post_data=login_params, session=self.session, timeout=self.url_timeout)
            if response and logged_in():
                return True

            msg = u'Failed to authenticate with %s, abort provider'
            if response and 'Username or password incorrect' in response:
                msg = u'Invalid username or password for %s. Check settings'
            logger.log(msg % self.name, logger.ERROR)

        return False

    def _do_search(self, search_params, search_mode='eponly', epcount=0, age=0):

        results = []
        if not self._do_login():
            return results

        items = {'Season': [], 'Episode': [], 'Cache': []}

        rc = dict((k, re.compile('(?i)' + v)) for (k, v) in {'info': 'detail', 'get': 'download',
                                                             'cats': 'cat=(?:7)'}.items())
        for mode in search_params.keys():
            for search_string in search_params[mode]:
                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                search_url = self.urls['search'] % (self.categories, search_string)
                html = self.get_url(search_url, timeout=self.url_timeout)

                cnt = len(items[mode])
                try:
                    if not html or self._has_no_results(html):
                        raise generic.HaltParseException

                    with BS4Parser(html, features=['html5lib', 'permissive']) as soup:
                        torrent_table = soup.find('td', attrs={'class': 'colhead'}).find_parent('table')
                        torrent_rows = [] if not torrent_table else torrent_table.find_all('tr')

                        if 2 > len(torrent_rows):
                            raise generic.HaltParseException

                        for tr in torrent_rows[1:]:
                            try:
                                info = tr.find('a', href=rc['info'])
                                if not info:
                                    continue

                                seeders, leechers = [int(tr.find_all('td')[x].get_text().strip()) for x in (-2, -1)]
                                if None is tr.find('a', href=rc['cats'])\
                                        or ('Cache' != mode and (seeders < self.minseed or leechers < self.minleech)):
                                    continue

                                title = 'title' in info.attrs and info.attrs['title'] or info.get_text().strip()
                                download_url = self.urls['get'] % tr.find('a', href=rc['get']).get('href')

                            except (AttributeError, TypeError):
                                continue

                            if title and download_url:
                                items[mode].append((title, download_url, seeders))

                except (generic.HaltParseException, AttributeError):
                    pass
                except Exception:
                    logger.log(u'Failed to parse. Traceback: %s' % traceback.format_exc(), logger.ERROR)

                self._log_result(mode, len(items[mode]) - cnt, search_url)

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[2], reverse=True)

            results += items[mode]

        return results

    def find_propers(self, search_date=datetime.datetime.today()):

        return self._find_propers(search_date)

    def _get_episode_search_strings(self, ep_obj, add_string='', **kwargs):

        return generic.TorrentProvider._get_episode_search_strings(self, ep_obj, add_string, use_or=False)


class FunFileCache(tvcache.TVCache):

    def __init__(self, this_provider):
        tvcache.TVCache.__init__(self, this_provider)

        self.minTime = 15  # cache update frequency

    def _getRSSData(self):

        return self.provider.get_cache_data()


provider = FunFileProvider()
