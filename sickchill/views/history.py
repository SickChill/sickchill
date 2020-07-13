# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, print_function, unicode_literals

# First Party Imports
import sickbeard
from sickbeard import ui
from sickchill.helper import try_int
from sickchill.show.History import History as HistoryTool

# Local Folder Imports
from .common import PageTemplate
from .index import WebRoot
from .routes import Route


@Route('/history(/?.*)', name='history')
class History(WebRoot):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)

        self.history = HistoryTool()

    def index(self, limit=None):
        sickbeard.HISTORY_LIMIT = limit = try_int(limit or sickbeard.HISTORY_LIMIT or 100, 100)
        sickbeard.save_config()

        compact = []
        data = self.history.get(limit)

        for row in data:
            action = {
                'action': row['action'],
                'provider': row['provider'],
                'resource': row['resource'],
                'time': row['date']
            }

            # noinspection PyTypeChecker
            if not any((history['show_id'] == row['show_id'] and
                        history['season'] == row['season'] and
                        history['episode'] == row['episode'] and
                        history['quality'] == row['quality']) for history in compact):
                history = {
                    'actions': [action],
                    'episode': row['episode'],
                    'quality': row['quality'],
                    'resource': row['resource'],
                    'season': row['season'],
                    'show_id': row['show_id'],
                    'show_name': row['show_name']
                }

                compact.append(history)
            else:
                index = [
                    i for i, item in enumerate(compact)
                    if item['show_id'] == row['show_id'] and
                    item['season'] == row['season'] and
                    item['episode'] == row['episode'] and
                    item['quality'] == row['quality']
                ][0]
                history = compact[index]
                history['actions'].append(action)
                history['actions'].sort(key=lambda x: x['time'], reverse=True)

        t = PageTemplate(rh=self, filename="history.mako")
        submenu = [
            {'title': _('Remove Selected'), 'path': 'history/removeHistory', 'icon': 'fa fa-eraser', 'class': 'removehistory', 'confirm': False},
            {'title': _('Clear History'), 'path': 'history/clearHistory', 'icon': 'fa fa-trash', 'class': 'clearhistory', 'confirm': True},
            {'title': _('Trim History'), 'path': 'history/trimHistory', 'icon': 'fa fa-scissors', 'class': 'trimhistory', 'confirm': True},
        ]

        return t.render(historyResults=data, compactResults=compact, limit=limit,
                        submenu=submenu, title=_('History'), header=_('History'),
                        topmenu="history", controller="history", action="index")

    def removeHistory(self, toRemove=None):
        logsToRemove = []
        for logItem in toRemove.split('|'):
            info = logItem.split(',')
            logsToRemove.append({
                'dates': info[0].split('$'),
                'show_id': info[1],
                'season': info[2],
                'episode': info[3]
            })

        self.history.remove(logsToRemove)

        ui.notifications.message(_('Selected history entries removed'))

        return self.redirect("/history/")

    def clearHistory(self):
        self.history.clear()

        ui.notifications.message(_('History cleared'))

        return self.redirect("/history/")

    def trimHistory(self):
        self.history.trim()

        ui.notifications.message(_('Removed history entries older than 30 days'))

        return self.redirect("/history/")
