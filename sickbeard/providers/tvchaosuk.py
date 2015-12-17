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
# from urllib import urlencode

import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard.helpers import sanitizeSceneName
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException
from sickrage.providers.TorrentProvider import TorrentProvider


class TVChaosUKProvider(TorrentProvider):
    def __init__(self):
        TorrentProvider.__init__(self, 'TvChaosUK')

        self.urls = {'base_url': 'https://tvchaosuk.com/',
                     'login': 'https://tvchaosuk.com/takelogin.php',
                     'index': 'https://tvchaosuk.com/index.php',
                     'search': 'https://tvchaosuk.com/browse.php'}

        self.url = self.urls['base_url']

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = None

        self.cache = TVChaosUKCache(self)

        self.search_params = {
            'do': 'search',
            'keywords':  '',
            'search_type': 't_name',
            'category': 0,
            'include_dead_torrents': 'no',
        }

    def _check_auth(self):
        if self.username and self.password:
            return True

        raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}

        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            for sep in ' ', ' - ':
                season_string = show_name + sep + 'Series '
                if ep_obj.show.air_by_date or ep_obj.show.sports:
                    season_string += str(ep_obj.airdate).split('-')[0]
                elif ep_obj.show.anime:
                    season_string += '%d' % ep_obj.scene_absolute_number
                else:
                    season_string += '%d' % int(ep_obj.scene_season)

                search_string['Season'].append(re.sub(r'\s+', ' ', season_string.replace('.', ' ').strip()))

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            for sep in ' ', ' - ':
                ep_string = sanitizeSceneName(show_name) + sep
                if self.show.air_by_date:
                    ep_string += str(ep_obj.airdate).replace('-', '|')
                elif self.show.sports:
                    ep_string += str(ep_obj.airdate).replace('-', '|') + '|' + ep_obj.airdate.strftime('%b')
                elif self.show.anime:
                    ep_string += '%i' % int(ep_obj.scene_absolute_number)
                else:
                    ep_string += sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season, 'episodenumber': ep_obj.scene_episode}

                if add_string:
                    ep_string += ' %s' % add_string

                search_string['Episode'].append(re.sub(r'\s+', ' ', ep_string.replace('.', ' ').strip()))

        return [search_string]

    def login(self):

        login_params = {'username': self.username, 'password': self.password}
        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Error: Username or password incorrect!', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self.login():
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params['keywords'] = search_string.strip()
                data = self.get_url(self.urls['search'], params=self.search_params)
                # url_searched = self.urls['search'] + '?' + urlencode(self.search_params)

                if not data:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                with BS4Parser(data) as html:
                    torrent_table = html.find(id='listtorrents')
                    if not torrent_table:
                        logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                        continue

                    torrent_rows = torrent_table.find_all('tr')

                    for torrent in torrent_rows:
                        try:
                            cells = torrent.find_all('td')
                            freeleech = torrent.find('img', alt=re.compile('Free Torrent'))
                            if self.freeleech and not freeleech:
                                continue
                            title = (torrent.find(attrs={'class':'tooltip-target'}).text.strip()).replace("mp4", "x264")
                            download_url = torrent.find(title="Click to Download this Torrent!").parent['href'].strip()
                            seeders = int(torrent.find(title='Seeders').text.strip())
                            leechers = int(torrent.find(title='Leechers').text.strip())

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            # Chop off tracker/channel prefix or we cant parse the result!
                            show_name_first_word = re.search(r'^[^ .]+', self.search_params['keywords']).group()
                            if not title.startswith(show_name_first_word):
                                title = re.match(r'(.*)(' + show_name_first_word + '.*)', title).group(2)

                            # Change title from Series to Season, or we can't parse
                            if 'Series' in self.search_params['keywords']:
                                title = re.sub(r'(?i)series', 'Season', title)

                            # Strip year from the end or we can't parse it!
                            title = re.sub(r'[\. ]?\(\d{4}\)', '', title)

                            torrent_size = cells[4].getText().strip()
                            size = -1
                            if re.match(r"\d+([,\.]\d+)?\s*[KkMmGgTt]?[Bb]", torrent_size):
                                size = self._convertSize(torrent_size.rstrip())

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


    def _convertSize(self, sizeString):
        size = sizeString[:-2].strip()
        modifier = sizeString[-2:].upper()
        try:
            size = float(size)
            if modifier in 'KB':
                size = size * 1024
            elif modifier in 'MB':
                size = size * 1024**2
            elif modifier in 'GB':
                size = size * 1024**3
            elif modifier in 'TB':
                size = size * 1024**4
        except Exception:
            size = -1
        return int(size)


class TVChaosUKCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll TVChaosUK every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}


provider = TVChaosUKProvider()
