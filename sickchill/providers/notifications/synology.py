# coding=utf-8
# Author: Nyaran <nyayukko@gmail.com>
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
# Stdlib Imports
import os
import subprocess

# First Party Imports
import sickbeard
from sickbeard import common, logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def __init__(self):
        super().__init__('Synology')

    def notify_snatch(self, name):
        if self.config('snatch'):
            self._send_synologyNotifier(name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, name):
        if self.config('download'):
            self._send_synologyNotifier(name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._send_synologyNotifier(name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if self.config('update'):
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._send_synologyNotifier(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if self.config('login'):
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_synologyNotifier(update_text.format(ipaddress), title)

    def notify_postprocess(self, name: str):
        if self.config('process'):
            title = common.notifyStrings[common.NOTIFY_POSTPROCESS]
            self._send_synologyNotifier(name, title)

    def update_library(self, item, remove: bool = False):
        pass

    @staticmethod
    def test_notify(username):
        pass

    def _send_synologyNotifier(self, message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        logger.info("Executing command " + str(synodsmnotify_cmd))
        logger.debug("Absolute path to command: " + os.path.abspath(synodsmnotify_cmd[0]))
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 cwd=sickbeard.PROG_DIR)
            out, err = p.communicate()  # @UnusedVariable
            logger.debug("Script result: " + str(out))
        except OSError as e:
            logger.info("Unable to run synodsmnotify: " + str(e))
