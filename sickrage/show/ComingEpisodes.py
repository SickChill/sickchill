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
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import sickbeard

from datetime import date, timedelta
from sickbeard.common import WANTED, UNAIRED, Quality
from sickbeard.db import DBConnection
from sickbeard.network_timezones import parse_date_time
from sickbeard.sbdatetime import sbdatetime
from sickrage.helper.common import dateFormat, timeFormat
from sickrage.helper.quality import get_quality_string
from operator import itemgetter


class ComingEpisodes(object):
    """
    Missed:   yesterday...(less than 1 week)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """
    categories = ['later', 'missed', 'snatched', 'soon', 'today']
    sorts = {
        'date': (lambda a, b: a[b'localtime'] < b[b'localtime']),
        'network': (lambda a, b: (a[b'network'], a[b'localtime']) < (b[b'network'], b[b'localtime'])),
        'show': (lambda a, b: (a[b'show_name'], a[b'localtime']) < (b[b'show_name'], b[b'localtime'])),
    }

    def __init__(self):
        pass

    @staticmethod
    def get_coming_episodes(categories, sort, group, paused=sickbeard.COMING_EPS_DISPLAY_PAUSED):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpisodes.sorts``
        :param group: ``True`` to group the coming episodes by category, ``False`` otherwise
        :param paused: ``True`` to include paused shows, ``False`` otherwise
        :return: The list of coming episodes
        """

        categories = ComingEpisodes._get_categories(categories)
        sort = ComingEpisodes._get_sort(sort)

        today = date.today().toordinal()
        recently = (date.today() - timedelta(days=sickbeard.COMING_EPS_MISSED_RANGE)).toordinal()
        next_week = (date.today() + timedelta(days=7)).toordinal()

        db = DBConnection(row_type='dict')
        fields_to_select = ', '.join(
            ['airdate', 'airs', 'e.description as description', 'episode', 'imdb_id', 'e.indexer', 'indexer_id', 'e.location', 'name', 'network',
             'paused', 'quality', 'runtime', 'season', 'show_name', 'showid', 'e.status as epstatus', 's.status']
        )

        status_list = [WANTED, UNAIRED] + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        sql_l = []
        for show_obj in sickbeard.showList:
            next_air_date = show_obj.nextEpisode()
            sql_l.append(
                [
                    'SELECT DISTINCT {0} '.format(fields_to_select) +
                    'FROM tv_episodes e, tv_shows s '
                    'WHERE showid = ? '
                    'AND airdate <= ? '
                    'AND airdate >= ? '
                    'AND s.indexer_id = e.showid '
                    'AND e.status IN (' + ','.join(['?'] * len(status_list)) + ')',
                    [show_obj.indexerid, next_air_date or today, recently] + status_list
                ]
            )

        results = []
        for sql_i in sql_l:
            if results:
                results += db.select(*sql_i)
            else:
                results = db.select(*sql_i)

        for index, item in enumerate(results):
            results[index][b'localtime'] = sbdatetime.convert_to_setting(
                parse_date_time(item[b'airdate'], item[b'airs'], item[b'network']))

        results.sort(key=itemgetter(b'localtime'))
        results.sort(ComingEpisodes.sorts[sort])

        if not group:
            return results

        grouped_results = ComingEpisodes._get_categories_map(categories)

        for result in results:
            if result[b'paused'] and not paused:
                continue

            result[b'airs'] = str(result[b'airs']).replace('am', ' AM').replace('pm', ' PM').replace('  ', ' ')
            result[b'airdate'] = result[b'localtime'].toordinal()

            if int(result[b'epstatus']) in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST:
                if result[b'location']:
                    continue
                else:
                    category = 'snatched'
            elif result[b'airdate'] < today:
                category = 'missed'
            elif result[b'airdate'] >= next_week:
                category = 'later'
            elif result[b'airdate'] == today:
                category = 'today'
            else:
                category = 'soon'

            if len(categories) > 0 and category not in categories:
                continue

            if not result[b'network']:
                result[b'network'] = ''

            result[b'quality'] = get_quality_string(result[b'quality'])
            result[b'airs'] = sbdatetime.sbftime(result[b'localtime'], t_preset=timeFormat).lstrip('0').replace(' 0', ' ')
            result[b'weekday'] = 1 + result[b'localtime'].weekday()
            result[b'tvdbid'] = result[b'indexer_id']
            result[b'airdate'] = sbdatetime.sbfdate(result[b'localtime'], d_preset=dateFormat)
            result[b'localtime'] = result[b'localtime'].toordinal()

            grouped_results[category].append(result)

        return grouped_results

    @staticmethod
    def _get_categories(categories):
        if not categories:
            return []

        if not isinstance(categories, list):
            return categories.split('|')

        return categories

    @staticmethod
    def _get_categories_map(categories):
        if not categories:
            return {}

        return {category: [] for category in categories}

    @staticmethod
    def _get_sort(sort):
        sort = sort.lower() if sort else ''

        if sort not in ComingEpisodes.sorts.keys():
            return 'date'

        return sort
