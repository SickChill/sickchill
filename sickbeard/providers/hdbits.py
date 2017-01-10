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
from requests.compat import urlencode, urljoin

from sickbeard import classes, logger, tvcache

from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

try:
    import json
except ImportError:
    import simplejson as json


class HDBitsProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "HDBits")

        self.username = None
        self.passkey = None

        self.cache = HDBitsCache(self, min_time=15)  # only poll HDBits every 15 minutes max

        self.url = 'https://hdbits.org'
        self.urls = {
            'search': urljoin(self.url, '/api/torrents'),
            'rss': urljoin(self.url, '/api/torrents'),
            'download': urljoin(self.url, '/download.php')
        }

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, parsedJSON):

        if 'status' in parsedJSON and 'message' in parsedJSON:
            if parsedJSON.get('status') == 5:
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
        url = self.urls['download'] + '?' + urlencode({'id': item['id'], 'passkey': self.passkey})

        return title, url

    def search(self, search_params, age=0, ep_obj=None):

        # FIXME
        results = []

        logger.log(u"Search string: {0}".format
                   (search_params.decode('utf-8')), logger.DEBUG)

        self._check_auth()

        parsedJSON = self.get_url(self.urls['search'], post_data=search_params, returns='json')
        if not parsedJSON:
            return []

        if self._checkAuthFromData(parsedJSON):
            if parsedJSON and 'data' in parsedJSON:
                items = parsedJSON['data']
            else:
                logger.log(u"Resulting JSON from provider isn't correct, not parsing it", logger.ERROR)
                items = []

            for item in items:
                results.append(item)
        # FIXME SORTING
        return results

    def find_propers(self, search_date=None):
        results = []

        search_terms = [' proper ', ' repack ']

        for term in search_terms:
            for item in self.search(self._make_post_data_JSON(search_term=term)):
                if item['utadded']:
                    try:
                        result_date = datetime.datetime.fromtimestamp(int(item['utadded']))
                    except Exception:
                        result_date = None

                    if result_date:
                        if not search_date or result_date > search_date:
                            title, url = self._get_title_and_url(item)
                            results.append(classes.Proper(title, url, result_date, self.show))

        return results

    def _make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None):

        post_data = {
            'username': self.username,
            'passkey': self.passkey,
            'category': [2],
            # TV Category
        }

        if episode:
            if show.air_by_date:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': str(episode.airdate).replace('-', '|')
                }
            elif show.sports:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': episode.airdate.strftime('%b')
                }
            elif show.anime:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': "{0:03d}".format(int(episode.scene_absolute_number))
                }
            else:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': episode.scene_season,
                    'episode': episode.scene_episode
                }

        if season:
            if show.air_by_date or show.sports:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': str(season.airdate)[:7],
                }
            elif show.anime:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': "{0:03d}".format(season.scene_absolute_number),
                }
            else:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': season.scene_season,
                }

        if search_term:
            post_data['search'] = search_term

        return json.dumps(post_data)


class HDBitsCache(tvcache.TVCache):
    def _getRSSData(self):
        self.search_params = None  # HDBits cache does not use search_params so set it to None
        results = []

        try:
            parsedJSON = self.provider.getURL(self.provider.urls['rss'], post_data=self.provider._make_post_data_JSON(), returns='json')

            if self.provider._checkAuthFromData(parsedJSON):
                results = parsedJSON['data']
        except Exception:
            pass

        return {'entries': results}

provider = HDBitsProvider()
