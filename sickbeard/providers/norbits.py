# coding=utf-8
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

import datetime
from requests.compat import urlencode

from sickbeard import classes, logger, tvcache

from sickbeard.helpers import sanitizeSceneName
from sickrage.helper.common import episode_num
from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

try:
    import json
except ImportError:
    import simplejson as json


class NorbitsProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Norbits")

        self.username = None
        self.passkey = None
        self.ratio = None

        self.cache = NorbitsCache(self, min_time=15)  # only poll Norbits every 15 minutes max

        self.urls = {'base_url': 'https://norbits.net',
                     'search': 'https://norbits.net/api2.php?action=torrents',
                     'download': 'https://norbits.net/download.php?'}

        self.url = self.urls['base_url']

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, parsedJSON):

        if 'status' in parsedJSON and 'message' in parsedJSON:
            if parsedJSON.get('status') == 3:
                logger.log(u"Invalid username or password. Check your settings", logger.WARNING)

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

        # FIXME
        results = []

        logger.log(u"Search string: %s" % search_params, logger.DEBUG)

        self._check_auth()
        parsedJSON = self.get_url(self.urls['search'], post_data=search_params, json=True)
        if not parsedJSON:
            return []

        if self._checkAuthFromData(parsedJSON):
            if parsedJSON and 'data' in parsedJSON:
                items = parsedJSON['data']
            else:
                logger.log(u"Resulting JSON from provider isn't correct, not parsing it", logger.ERROR)
                items = []
            if 'torrents' in items:
                for item in items['torrents']:
                    results.append(item)
        # FIXME SORTING
        logger.log(u'results: %s' % results, logger.DEBUG)
        return results


    def _make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None):
        post_data = {
            'username': self.username,
            'passkey': self.passkey,
            'category': '2',
            # TV Category
        }
        ep_num = episode_num(episode.scene_season, episode.scene_episode)
        show_name = sanitizeSceneName(episode.show.name)
        search = "%s.%s" % (show_name, ep_num)
        post_data['search'] = search

        if search_term:
            post_data['search'] = search_term

        return json.dumps(post_data)

    def seed_ratio(self):
        return self.ratio


class NorbitsCache(tvcache.TVCache):
    def _getRSSData(self):
        self.search_params = None  # Norbits cache does not use search_params so set it to None
        results = []

        try:
            parsedJSON = self.provider.getURL(self.provider.urls['rss'], post_data=self.provider._make_post_data_JSON(), returns='json')

            if self.provider._checkAuthFromData(parsedJSON):
                results = parsedJSON['data']
        except Exception:
            pass

        return {'entries': results}

provider = NorbitsProvider()
