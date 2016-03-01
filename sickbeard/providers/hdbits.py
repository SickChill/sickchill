# coding=utf-8
''' A HDBits (https://hdbits.org) provider'''
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

from requests.compat import urlencode, urljoin

from sickbeard import logger, tvcache

from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

try:
    import json
except ImportError:
    import simplejson as json


class HDBitsProvider(TorrentProvider): # pylint: disable=too-many-instance-attributes
    ''' Main provider object'''

    def __init__(self):
	'''Initialize the class'''

	# Provider Init
	TorrentProvider.__init__(self, 'HDBits')

	# Credentials
	self.username = None
	self.passkey = None

	# Torrent Stats
	self.ratio = None
	self.minseed = None
	self.minleech = None

	# URLs
	self.url = 'https://hdbits.org'
	self.urls = {'search': urljoin(self.url, '/api/torrents'),
		     'rss': urljoin(self.url, '/api/torrents'),
		     'download': urljoin(self.url, '/download.php?')}

	# Proper Strings
	self.proper_strings = ['PROPER', 'REPACK']

	# Cache
	self.cache = tvcache.TVCache(self, min_time=15)  # only poll HDBits every 15 minutes max

	# Logger to satisfy pylint
	self.logger = logger.Logger()

    def _check_auth(self):

	if not self.username or not self.passkey:
	    raise AuthException((u'Your authentication credentials for {} are missing, '
				 'check your config.').format(self.name))

	return True

    def _checkAuthFromData(self, parsed_json): # pylint: disable=invalid-name
	'''Check from the parsed resposne that we are autenticated'''

	if 'status' in parsed_json and 'message' in parsed_json:
	    if parsed_json.get('status') == 5:
		self.logger.log(u'Invalid username or password. Check your settings',
				logger.WARNING)

	return True

    def search(self, search_params, age=0, ep_obj=None): # pylint: disable=too-many-locals
	''' Do the actual searching and JSON parsing'''

	print('sp:', dir(search_params))
	print('eo:', dir(ep_obj))
	results = []
	for mode in search_params:
	    items = []
	    self.logger.log(u'Search Mode: {}'.format(mode), logger.DEBUG)

	    for search_string in search_params[mode]:
		if mode != 'RSS':
		    self.logger.log('Search String: {}'.format(search_string.decode('utf-8')),
				    logger.DEBUG)

		post_data = {
		    'username': self.username,
		    'passkey': self.passkey,
		    'category': [2], # TV Category
		    'search': search_string,
		}

		if mode != 'RSS':
		    post_data['tvdb'] = {'id': ep_obj.show['indexerid']}

		self._check_auth()
		parsed_json = self.get_url(self.urls['search'],
					   post_data=post_data,
					   json=True)

		if not parsed_json:
		    self.logger.log(u'Provider did not return expected result (not JSON)',
				    logger.DEBUG)
		    return []

		if self._checkAuthFromData(parsed_json):
		    if parsed_json and 'data' in parsed_json:
			json_items = parsed_json['data']
		    else:
			self.logger.log((u'Resulting JSON from provider is not correct, '
					 'not parsing it'), logger.ERROR)
			json_items = []

		    for item in json_items:
			seeders = item['seeders']
			leechers = item['leechers']
			title = item['name']
			info_hash = item['hash']
			size = item['size']
			download_url = ('{}{}'.format(self.urls['download'],
						      urlencode({'id': item['id'],
								 'passkey': self.passkey})))
			if seeders < self.minseed or leechers < self.minleech:
			    self.logger.log((u'Discarding torrent because it does not meet '
					     'the minimum seeders or leechers: '
					     '{} (S:{} L:{})'.format(title,
								     seeders,
								     leechers), logger.DEBUG))
			    continue
			else:
			    item = title, download_url, size, seeders, leechers, info_hash
			    if mode != "RSS":
				self.logger.log((u'Found result: {} with {} seeders and {}'
						 'leechers').format(title,
								    seeders,
								    leechers), logger.DEBUG)

			self.logger.log(u'item: {}'.format(item), logger.DEBUG)
			items.append(item)

	    # For each search mode sort all the items by seeders if available
	    items.sort(key=lambda tup: tup[3], reverse=True)
	    results += items

	return results


    def bla_make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None): # pylint: disable=invalid-name
	''' This should be removed'''

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
		    'episode': '%i' % int(episode.scene_absolute_number)
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
		    'season': '%d' % season.scene_absolute_number,
                }
            else:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': season.scene_season,
                }

        if search_term:
            post_data['search'] = search_term

        return json.dumps(post_data)

    def seed_ratio(self):
        return self.ratio

provider = HDBitsProvider() # pylint: disable=invalid-name
