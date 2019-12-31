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
# pylint: disable=abstract-method,too-many-lines, R

# Future Imports
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

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/history(/?.*)', name='history')
class History(WebRoot):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)

        self.history = HistoryTool()

    def index(self, limit=None):  # pylint: disable=arguments-differ
        sickbeard.HISTORY_LIMIT = limit = try_int(limit or sickbeard.HISTORY_LIMIT or 100, 100)
        sickbeard.save_config()

        compact = []
        data = self.history.get(limit)

        for row in data:
            action = {
                'action': row[b'action'],
                'provider': row[b'provider'],
                'resource': row[b'resource'],
                'time': row[b'date']
            }

            # noinspection PyTypeChecker
            if not any((history[b'show_id'] == row[b'show_id'] and
                        history[b'season'] == row[b'season'] and
                        history[b'episode'] == row[b'episode'] and
                        history[b'quality'] == row[b'quality']) for history in compact):
                history = {
                    'actions': [action],
                    'episode': row[b'episode'],
                    'quality': row[b'quality'],
                    'resource': row[b'resource'],
                    'season': row[b'season'],
                    'show_id': row[b'show_id'],
                    'show_name': row[b'show_name']
                }

                compact.append(history)
            else:
                index = [
                    i for i, item in enumerate(compact)
                    if item[b'show_id'] == row[b'show_id'] and
                    item[b'season'] == row[b'season'] and
                    item[b'episode'] == row[b'episode'] and
                    item[b'quality'] == row[b'quality']
                ][0]
                history = compact[index]
                history[b'actions'].append(action)
                history[b'actions'].sort(key=lambda x: x[b'time'], reverse=True)

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
