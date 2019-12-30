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

from __future__ import absolute_import, print_function, unicode_literals

import os
import time

from tornado.web import addslash

import sickbeard
from sickbeard import helpers
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from .index import Config

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/config/backuprestore(/?.*)', name='config:backup')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_backuprestore.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Backup/Restore'),
                        header=_('Backup/Restore'), topmenu='config',
                        controller="config", action="backupRestore")

    @staticmethod
    def backup(backupDir=None):

        finalResult = ''

        if backupDir:
            source = [ek(os.path.join, sickbeard.DATA_DIR, 'sickbeard.db'), sickbeard.CONFIG_FILE,
                      ek(os.path.join, sickbeard.DATA_DIR, 'failed.db'),
                      ek(os.path.join, sickbeard.DATA_DIR, 'cache.db')]
            target = ek(os.path.join, backupDir, 'sickchill-' + time.strftime('%Y%m%d%H%M%S') + '.zip')

            for (path, dirs, files) in ek(os.walk, sickbeard.CACHE_DIR, topdown=True):
                for dirname in dirs:
                    if path == sickbeard.CACHE_DIR and dirname not in ['images']:
                        dirs.remove(dirname)
                for filename in files:
                    source.append(ek(os.path.join, path, filename))

            if helpers.backup_config_zip(source, target, sickbeard.DATA_DIR):
                finalResult += "Successful backup to " + target
            else:
                finalResult += "Backup FAILED"
        else:
            finalResult += "You need to choose a folder to save your backup to!"

        finalResult += "<br>\n"

        return finalResult

    @staticmethod
    def restore(backupFile=None):

        finalResult = ''

        if backupFile:
            source = backupFile
            target_dir = ek(os.path.join, sickbeard.DATA_DIR, 'restore')

            if helpers.restore_config_zip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickchill to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br>\n"

        return finalResult
