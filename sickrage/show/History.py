# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

from datetime import datetime
from datetime import timedelta
from sickbeard.common import Quality
from sickbeard.db import DBConnection


class History:
    date_format = '%Y%m%d%H%M%S'

    def __init__(self):
        self.db = DBConnection()

    def clear(self):
        """
        Clear all the history
        """
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE 1 = 1'
        )

    def get(self, limit=100, action=None):
        """
        :param limit: The maximum number of elements to return
        :param action: The type of action to filter in the history. Either 'downloaded' or 'snatched'. Anything else or
                        no value will return everything (up to ``limit``)
        :return: The last ``limit`` elements of type ``action`` in the history
        """

        action = action.lower() if isinstance(action, str) else ''
        limit = int(limit)

        if action == 'downloaded':
            actions = Quality.DOWNLOADED
        elif action == 'snatched':
            actions = Quality.SNATCHED
        else:
            actions = []

        common_sql = 'SELECT action, date, episode, provider, h.quality, resource, season, show_name, showid ' \
                     'FROM history h, tv_shows s ' \
                     'WHERE h.showid = s.indexer_id '
        filter_sql = 'AND action in (' + ','.join(['?'] * len(actions)) + ') '
        order_sql = 'ORDER BY date DESC '

        if limit == 0:
            if len(actions) > 0:
                results = self.db.select(common_sql + filter_sql + order_sql, actions)
            else:
                results = self.db.select(common_sql + order_sql)
        else:
            if len(actions) > 0:
                results = self.db.select(common_sql + filter_sql + order_sql + 'LIMIT ?', actions + [limit])
            else:
                results = self.db.select(common_sql + order_sql + 'LIMIT ?', [limit])

        data = []
        for result in results:
            data.append({
                'action': result['action'],
                'date': result['date'],
                'episode': result['episode'],
                'provider': result['provider'],
                'quality': result['quality'],
                'resource': result['resource'],
                'season': result['season'],
                'show_id': result['showid'],
                'show_name': result['show_name']
            })

        return data

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """

        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE date < ?',
            [(datetime.today() - timedelta(days=30)).strftime(History.date_format)]
        )
