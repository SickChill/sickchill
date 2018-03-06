# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <https://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from datetime import datetime, timedelta

import six

from sickbeard.common import Quality
from sickbeard.db import DBConnection
from sickrage.helper.common import try_int


class History(object):
    date_format = '%Y%m%d%H%M%S'

    def __init__(self):
        self.db = DBConnection()

    def remove(self, toRemove):
        """
        Removes the selected history
        :param toRemove: Contains the properties of the log entries to remove
        """
        query = ''

        for item in toRemove:
            query = query + ' OR ' if query != '' else ''
            query = query + '(date IN ({0}) AND showid = {1} ' \
                            'AND season = {2} AND episode = {3})' \
                            .format(','.join(item['dates']), item['show_id'], \
                                    item['season'], item['episode'])

        self.db.action(
            'DELETE FROM history WHERE ' + query
        )

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

        actions = History._get_actions(action)
        limit = History._get_limit(limit)

        common_sql = 'SELECT action, date, episode, provider, h.quality, resource, season, show_name, showid ' \
                     'FROM history h, tv_shows s ' \
                     'WHERE h.showid = s.indexer_id '
        filter_sql = 'AND action in (' + ','.join(['?'] * len(actions)) + ') '
        order_sql = 'ORDER BY date DESC '

        if limit == 0:
            if actions:
                results = self.db.select(common_sql + filter_sql + order_sql, actions)
            else:
                results = self.db.select(common_sql + order_sql)
        else:
            if actions:
                results = self.db.select(common_sql + filter_sql + order_sql + 'LIMIT ?', actions + [limit])
            else:
                results = self.db.select(common_sql + order_sql + 'LIMIT ?', [limit])

        data = []
        for result in results:
            data.append({
                'action': result[b'action'],
                'date': result[b'date'],
                'episode': result[b'episode'],
                'provider': result[b'provider'],
                'quality': result[b'quality'],
                'resource': result[b'resource'],
                'season': result[b'season'],
                'show_id': result[b'showid'],
                'show_name': result[b'show_name']
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

    @staticmethod
    def _get_actions(action):
        action = action.lower() if isinstance(action, six.string_types) else ''

        if action == 'downloaded':
            return Quality.DOWNLOADED

        if action == 'snatched':
            return Quality.SNATCHED

        return []

    @staticmethod
    def _get_limit(limit):
        limit = try_int(limit, 0)

        return max(limit, 0)
