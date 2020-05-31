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

# Local Folder Imports
from .api import ApiCall, ApiHandler, function_mapper, KeyHandler
from .authentication import LoginHandler, LogoutHandler
from .browser import WebFileBrowser
from .calendar import CalendarHandler
from .changelog import HomeChangeLog
from .common import PageTemplate
from .config import (Config, ConfigAnime, ConfigBackupRestore, ConfigNotifications, ConfigPostProcessing, ConfigProviders, ConfigSearch, ConfigShares,
                     ConfigSubtitles)
from .history import History
from .home import Home
from .index import BaseHandler, WebHandler, WebRoot
from .irc import HomeIRC
from .logs import ErrorLogs
from .manage import AddShows, Manage, ManageSearches, PostProcess
from .news import HomeNews
from .routes import Route
