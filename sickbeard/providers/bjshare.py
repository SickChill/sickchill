# coding=utf-8
# Author: DarkSupremo <uilton.dev@gmail.com>
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

"""Provider code for BJ-Share."""

from __future__ import unicode_literals

import re

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar
from requests.utils import add_dict_to_cookiejar

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class BJShareProvider(TorrentProvider):
    """BJ-Share Torrent provider."""

    def __init__(self):
        """Initialize the class."""
        super(BJShareProvider, self).__init__('BJ-Share')

        # URLs
        self.url = 'https://bj-share.me'
        self.urls = {
            'login': "https://bj-share.me/login.php",
            'search': urljoin(self.url, 'torrents.php')
        }

        # Credentials
        self.enable_cookies = True
        self.cookies = ''
        self.username = None
        self.password = None
        self.required_cookies = ['session']

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Miscellaneous Options
        self.supports_absolute_numbering = True
        self.max_back_pages = 2

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        # Cache
        self.cache = tvcache.TVCache(self)

        # One piece and Boruto is the only animes that i'm aware that is in "absolute" numbering, the problem is that
        # they include the season (wrong season) and episode as absolute, eg: One Piece - S08E836
        # 836 is the latest episode in absolute numbering, that is correct, but S08 is not the current season...
        # So for this show, i don't see a other way to make it work...
        #
        # All others animes that i tested is with correct season and episode set, so i can't remove the season from all
        # or will break everything else
        #
        # In this indexer, it looks that it is added "automatically", so all current and new releases will be broken
        # until they or the source from where they get that info fix it...
        self.absolute_numbering = [
            'One Piece', 'Boruto: Naruto Next Generations'
        ]

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Informations about the episode being searched (when not RSS)

        :returns: A list of search results (structure)
        """
        results = []
        if not self.login():
            return results

        anime = False
        if ep_obj and ep_obj.show:
            anime = ep_obj.show.anime == 1

        search_params = {
            'order_by': 'time',
            'order_way': 'desc',
            'group_results': 0,
            'action': 'basic',
            'searchsubmit': 1
        }

        if 'RSS' in search_strings.keys():
            search_params['filter_cat[14]'] = 1  # anime
            search_params['filter_cat[2]'] = 1  # tv shows
        elif anime:
            search_params['filter_cat[14]'] = 1  # anime
        else:
            search_params['filter_cat[2]'] = 1  # tv shows

        for mode in search_strings:
            items = []
            logger.log(u'Search Mode: {0}'.format(mode), logger.DEBUG)

            # if looking for season, look for more pages
            if mode == 'Season':
                self.max_back_pages = 10

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u'Search string: {0}'.format(search_string.decode('utf-8')), logger.DEBUG)

                # Remove season / episode from search (not supported by tracker)
                search_str = re.sub(r'\d+$' if anime else r'[S|E]\d\d', '', search_string).strip()
                search_params['searchstr'] = search_str
                next_page = 1
                has_next_page = True

                while has_next_page and next_page <= self.max_back_pages:
                    search_params['page'] = next_page
                    logger.log(u'Page Search: {0}'.format(next_page), logger.DEBUG)
                    next_page += 1

                    response = self.session.get(self.urls['search'], params=search_params)
                    if not response:
                        logger.log('No data returned from provider', logger.DEBUG)
                        continue

                    result = self._parse(response.content, mode)
                    has_next_page = result['has_next_page']
                    items += result['items']

                results += items

        return results

    def _parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A KV with a list of items found and if there's an next page to search
        """

        def process_column_header(td):
            ret = u''
            if td.a and td.a.img:
                ret = td.a.img.get('title', td.a.get_text(strip=True))
            if not ret:
                ret = td.get_text(strip=True)
            return ret

        items = []
        has_next_page = False
        with BS4Parser(data, 'html5lib') as html:
            torrent_table = html.find('table', id='torrent_table')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # ignore next page in RSS mode
            has_next_page = mode != 'RSS' and html.find('a', class_='pager_next') is not None
            logger.log(u'More Pages? {0}'.format(has_next_page), logger.DEBUG)

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                return {'has_next_page': has_next_page, 'items': []}

            # '', '', 'Name /Year', 'Files', 'Time', 'Size', 'Snatches', 'Seeders', 'Leechers'
            labels = [process_column_header(label) for label in torrent_rows[0]('td')]
            group_title = u''

            # Skip column headers
            for result in torrent_rows[1:]:
                cells = result('td')
                result_class = result.get('class')
                # When "Grouping Torrents" is enabled, the structure of table change
                group_index = -2 if 'group_torrent' in result_class else 0
                try:
                    title = result.select('a[href^="torrents.php?id="]')[0].get_text()
                    title = re.sub('\s+', ' ', title).strip()  # clean empty lines and multiple spaces

                    if 'group' in result_class or 'torrent' in result_class:
                        # get international title if available
                        title = re.sub('.* \[(.*?)\](.*)', r'\1\2', title)

                    if 'group' in result_class:
                        group_title = title
                        continue

                    # Clean dash between title and season/episode
                    title = re.sub('- (S\d{2}(E\d{2,4})?)', r'\1', title)

                    for serie in self.absolute_numbering:
                        if serie in title:
                            # remove season from title when its in absolute format
                            title = re.sub('S\d{2}E(\d{2,4})', r'\1', title)
                            break

                    download_url = urljoin(self.url,
                                           result.select('a[href^="torrents.php?action=download"]')[0]['href'])
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index('Seeders') + group_index].get_text(strip=True))
                    leechers = try_int(cells[labels.index('Leechers') + group_index].get_text(strip=True))

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != "RSS":
                            logger.log("Discarding torrent because it doesn't meet the"
                                       " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                       (title, seeders, leechers), logger.DEBUG)
                        continue

                    torrent_details = None
                    if 'group_torrent' in result_class:
                        # torrents belonging to a group
                        torrent_details = title
                        title = group_title
                    elif 'torrent' in result_class:
                        # standalone/un grouped torrents
                        torrent_details = cells[labels.index('Nome/Ano')].find('div', class_='torrent_info').get_text()

                    torrent_details = torrent_details.replace('[', ' ').replace(']', ' ').replace('/', ' ')
                    torrent_details = torrent_details.replace('Full HD ', '1080p').replace('HD ', '720p')

                    torrent_size = cells[labels.index('Tamanho') + group_index].get_text(strip=True)
                    size = convert_size(torrent_size) or -1

                    torrent_name = '{0} {1}'.format(title, torrent_details.strip()).strip()
                    torrent_name = re.sub('\s+', ' ', torrent_name)

                    items.append({
                        'title': torrent_name,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers,
                        'hash': ''
                    })

                    if mode != 'RSS':
                        logger.log('Found result: {0} with {1} seeders and {2} leechers'.format
                                   (torrent_name, seeders, leechers), logger.DEBUG)

                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    logger.log('Failed parsing provider.', logger.ERROR)

        return {'has_next_page': has_next_page, 'items': items}

    def login(self):
        """Login method used for logging in before doing a search and torrent downloads."""
        cookie_dict = dict_from_cookiejar(self.session.cookies)
        if cookie_dict.get('session'):
            return True

        if self.cookies:
            add_dict_to_cookiejar(self.session.cookies, dict(x.rsplit('=', 1) for x in self.cookies.split(';')))

        cookie_dict = dict_from_cookiejar(self.session.cookies)
        if cookie_dict.get('session'):
            return True

        login_params = {
            'submit': 'Login',
            'username': self.username,
            'password': self.password,
            'keeplogged': 1,
        }

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('<title>Login :: BJ-Share</title>', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True


provider = BJShareProvider()
