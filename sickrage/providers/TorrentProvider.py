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

import sickbeard

from sickbeard.classes import TorrentSearchResult
from sickrage.helper.common import try_int
from sickrage.providers.GenericProvider import GenericProvider


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.provider_type = GenericProvider.TORRENT

    def find_propers(self, search_date=None):
        # TODO
        pass

    def is_active(self):
        return sickbeard.USE_TORRENTS and self.is_enabled()

    @staticmethod
    def _clean_title(title):
        if not title:
            return ''

        return title.replace(' ', '.')

    def _custom_trackers(self):
        # TODO
        pass

    def _get_episode_search_strings(self, episode, add_string=''):
        # TODO
        pass

    def _get_result(self, episodes):
        return TorrentSearchResult(episodes)

    def _get_season_search_strings(self, episode):
        # TODO
        pass

    def _get_size(self, item):
        if isinstance(item, dict):
            size = item.get('size', -1)
        elif isinstance(item, (list, tuple)) and len(item) > 2:
            size = item[2]
        else:
            size = -1

        # Make sure we didn't select seeds/leechers by accident
        if not size or size < 1024 * 1024:
            size = -1

        return try_int(size, -1)

    def _get_title_and_url(self, item):
        # TODO
        pass
