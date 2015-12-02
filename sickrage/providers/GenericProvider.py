# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

from abc import abstractmethod
from datetime import datetime
from random import shuffle
from requests import Session
from sickbeard.classes import Proper, SearchResult
from sickbeard.common import Quality, user_agents
from sickbeard.helpers import getURL
from sickbeard.tvcache import TVCache


class GenericProvider:
    NZB = 'nzb'
    TORRENT = 'torrent'

    def __init__(self, name):
        shuffle(user_agents)

        self.anime_only = False
        self.bt_cache_urls = []  # TODO
        self.cache = TVCache(self)
        self.enable_backlog = False
        self.enable_daily = False
        self.enabled = False
        self.headers = {
            'User-Agent': user_agents[0]
        }
        self.name = name
        self.proper_strings = ['PROPER|REPACK|REAL']
        self.provider_type = None
        self.public = False
        self.search_fallback = False
        self.search_mode = None
        self.session = Session()
        self.show = None
        self.supports_absolute_numbering = False
        self.supports_backlog = True
        self.url = ''
        self.urls = {}

        shuffle(self.bt_cache_urls)

    def download_result(self, result):
        # TODO
        pass

    def find_propers(self, search_date=None):
        results = self.cache.listPropers(search_date)

        return [Proper(x['name'], x['url'], datetime.fromtimestamp(x['time']), self.show) for x in results]

    def find_search_results(self, show, episodes, search_mode, manual_search=False, download_current_quality=False):
        # TODO
        pass

    def get_id(self):
        return GenericProvider.make_id(self.name)

    def get_quality(self, item, anime=False):
        (title, url) = self._get_title_and_url(item)
        quality = Quality.sceneQuality(title, anime)

        return quality

    def get_result(self, episodes):
        result = self._get_result(episodes)
        result.provider = self

        return result

    def get_url(self, url, post_data=None, params=None, timeout=30, json=False, need_bytes=False):
        return getURL(url, post_data=post_data, params=params, headers=self.headers, timeout=timeout,
                      session=self.session, json=json, needBytes=need_bytes)

    def image_name(self):
        return self.get_id() + '.png'

    def is_active(self):
        return False

    def is_enabled(self):
        return self.enabled

    @staticmethod
    def make_id(name):
        return re.sub(r'[^\w\d_]', '_', name.strip().lower())

    def search_rss(self, episodes):
        return self.cache.findNeededEpisodes(episodes)

    def seed_ratio(self):
        return ''

    def _check_auth(self):
        return True

    def _do_login(self):
        return True

    def _do_search(self, search_params, search_mode='eponly', episode_count=0, age=0, episode=None):
        return []

    @abstractmethod
    def _get_result(self, episodes):
        return SearchResult(episodes)

    def _get_episode_search_strings(self, episode, add_string=''):
        return []

    def _get_season_search_strings(self, episode):
        return []

    def _get_size(self, item):
        return -1

    def _get_title_and_url(self, item):
        # TODO
        pass

    def _make_url(self, result):
        # TODO
        pass

    def _verify_download(self, file_name=None):
        # TODO
        pass
