# coding=utf-8
'''A Norbits (https://norbits.net) provider, based on hdbits.py'''

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

from requests.compat import urlencode

from sickbeard import logger, tvcache

from sickbeard.helpers import sanitizeSceneName
from sickrage.helper.common import episode_num
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

try:
    import json
except ImportError:
    import simplejson as json


class NorbitsProvider(TorrentProvider):
    '''Main provider object'''

    def __init__(self):
        ''' Initialize the class '''
        TorrentProvider.__init__(self, 'Norbits')

        self.username = None
        self.passkey = None
        self.ratio = None

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll Norbits every 15 minutes max

        self.urls = {'base_url': 'https://norbits.net',
                     'search': 'https://norbits.net/api2.php?action=torrents',
                     'download': 'https://norbits.net/download.php?'}

        self.url = self.urls['base_url']
        self.logger = logger.Logger()

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException(('Your authentication credentials for %s are '
                                 'missing, check your config.') % self.name)

        return True

    def _checkAuthFromData(self, parsed_json):  # pylint: disable=invalid-name
        ''' Check that we are authenticated. '''

        if 'status' in parsed_json and 'message' in parsed_json:
            if parsed_json.get('status') == 3:
                self.logger.log((u'Invalid username or password. '
                                 'Check your settings'), logger.WARNING)

        return True

    def _get_season_search_strings(self, ep_obj):
        season_search_string = [self._make_post_data_JSON(show=ep_obj.show, season=ep_obj)]
        return season_search_string

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        episode_search_string = [self._make_post_data_JSON(show=ep_obj.show, episode=ep_obj)]
        return episode_search_string

    def _get_title_and_url(self, item):
        title = item.get('name', '').replace(' ', '.')
        url = self.urls['download'] + urlencode({'id': item['id'], 'passkey': self.passkey})
        return title, url

    def search(self, search_params, age=0, ep_obj=None):
        ''' Do the actual searching and JSON parsing'''

        results = []

        self.logger.log(u'Search string: %s' % search_params, logger.DEBUG)

        self._check_auth()
        parsed_json = self.get_url(self.urls['search'], post_data=search_params, json=True)
        if not parsed_json:
            return []

        if self._checkAuthFromData(parsed_json):
            if parsed_json and 'data' in parsed_json:
                items = parsed_json['data']
            else:
                self.logger.log((u'Resulting JSON from provider is not correct, '
                                 'not parsing it'), logger.ERROR)
                items = []
            if 'torrents' in items:
                for item in items['torrents']:
                    results.append(item)
        self.logger.log(u'results: %s' % results, logger.DEBUG)
        return results

    def _make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None):  # pylint: disable=invalid-name
        ''' Make post data for our JSON query'''
        post_data = {
            'username': self.username,
            'passkey': self.passkey,
            'category': '2',
            # TV Category
        }
        if episode:
            ep_num = episode_num(episode.scene_season, episode.scene_episode)
            show_name = sanitizeSceneName(show.name)
            search = '%s.%s' % (show_name, ep_num)
            post_data['search'] = search

        if season:
            self.logger.log(u'season: %s' % dir(season), logger.DEBUG)
        if search_term:
            post_data['search'] = search_term

        return json.dumps(post_data)

    def seed_ratio(self):
        return self.ratio


class NorbitsCache(tvcache.TVCache):
    ''' Hold our cache'''

    def _getRSSData(self):
        ''' We don't want to do RSS searchs'''
        pass

provider = NorbitsProvider()  # pylint: disable=invalid-name
