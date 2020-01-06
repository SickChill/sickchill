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

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import classes, logger, ui
from sickchill.helper import try_int

# Local Folder Imports
from .common import PageTemplate
from .index import WebRoot
from .routes import Route


@Route('/errorlogs(/?.*)', name='logs:error')
class ErrorLogs(WebRoot):
    def __init__(self, *args, **kwargs):
        super(ErrorLogs, self).__init__(*args, **kwargs)

    def ErrorLogsMenu(self, level):
        menu = [
            {
                'title': _('Clear Errors'),
                'path': 'errorlogs/clearerrors/',
                'requires': self.haveErrors() and level == logger.ERROR,
                'icon': 'ui-icon ui-icon-trash'
            },
            {
                'title': _('Clear Warnings'),
                'path': 'errorlogs/clearerrors/?level=' + str(logger.WARNING),
                'requires': self.haveWarnings() and level == logger.WARNING,
                'icon': 'ui-icon ui-icon-trash'
            },
            {
                'title': _('Submit Errors'),
                'path': 'errorlogs/submit_errors/',
                'requires': self.haveErrors() and level == logger.ERROR,
                'class': 'submiterrors',
                'confirm': True,
                'icon': 'ui-icon ui-icon-arrowreturnthick-1-n'
            },
        ]

        return menu

    @addslash
    def index(self, level=logger.ERROR):
        level = try_int(level, logger.ERROR)

        t = PageTemplate(rh=self, filename="errorlogs.mako")
        return t.render(header=_("Logs &amp; Errors"), title=_("Logs &amp; Errors"),
                        topmenu="system", submenu=self.ErrorLogsMenu(level),
                        logLevel=level, controller="errorlogs", action="index")

    @staticmethod
    def haveErrors():
        return len(classes.ErrorViewer.errors) > 0

    @staticmethod
    def haveWarnings():
        return len(classes.WarningViewer.errors) > 0

    def clearerrors(self, level=logger.ERROR):
        if int(level) == logger.WARNING:
            classes.WarningViewer.clear()
        else:
            classes.ErrorViewer.clear()

        return self.redirect("/errorlogs/viewlog/")

    def viewlog(self, min_level=logger.INFO, log_filter="<NONE>", log_search='', max_lines=500):
        data = sickbeard.logger.log_data(min_level, log_filter, log_search, max_lines)

        t = PageTemplate(rh=self, filename="viewlogs.mako")
        return t.render(
            header=_("Log File"), title=_("Logs"), topmenu="system",
            log_data="".join(data), min_level=min_level,
            log_filter=log_filter, log_search=log_search,
            controller="errorlogs", action="viewlogs")

    def submit_errors(self):
        submitter_result, issue_id = logger.submit_errors()
        logger.log(submitter_result, (logger.INFO, logger.WARNING)[not issue_id])
        submitter_notification = ui.notifications.error if not issue_id else ui.notifications.message
        submitter_notification(submitter_result)

        return self.redirect("/errorlogs/")
