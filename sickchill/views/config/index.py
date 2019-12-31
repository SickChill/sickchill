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

# Stdlib Imports
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard.versionChecker import CheckVersion
from sickchill.views.common import PageTemplate
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route('/config(/?.*)', name='config:main')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': _('General'), 'path': 'config/general/', 'icon': 'fa fa-cog'},
            {'title': _('Backup/Restore'), 'path': 'config/backuprestore/', 'icon': 'fa fa-floppy-o'},
            {'title': _('Search Settings'), 'path': 'config/search/', 'icon': 'fa fa-search'},
            {'title': _('Search Providers'), 'path': 'config/providers/', 'icon': 'fa fa-plug'},
            {'title': _('Subtitles Settings'), 'path': 'config/subtitles/', 'icon': 'fa fa-language'},
            {'title': _('Post Processing'), 'path': 'config/postProcessing/', 'icon': 'fa fa-refresh'},
            {'title': _('Notifications'), 'path': 'config/notifications/', 'icon': 'fa fa-bell-o'},
            {'title': _('Anime'), 'path': 'config/anime/', 'icon': 'fa fa-eye'},
        ]

        return menu

    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config.mako")

        try:
            # noinspection PyUnresolvedReferences
            import pwd
            sr_user = pwd.getpwuid(os.getuid()).pw_name
        except ImportError:
            try:
                import getpass
                sr_user = getpass.getuser()
            except StandardError:
                sr_user = 'Unknown'

        try:
            import locale
            sr_locale = locale.getdefaultlocale()
        except StandardError:
            sr_locale = 'Unknown', 'Unknown'

        try:
            import ssl
            ssl_version = ssl.OPENSSL_VERSION
        except StandardError:
            ssl_version = 'Unknown'

        sr_version = ''
        if sickbeard.VERSION_NOTIFY:
            updater = CheckVersion().updater
            if updater:
                updater.need_update()
                sr_version = updater.get_cur_version()

        return t.render(
            submenu=self.ConfigMenu(), title=_('SickChill Configuration'),
            header=_('SickChill Configuration'), topmenu="config",
            sr_user=sr_user, sr_locale=sr_locale, ssl_version=ssl_version,
            sr_version=sr_version
        )
