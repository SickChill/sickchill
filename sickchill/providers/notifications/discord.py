# coding=utf-8
# Author: Mhynlo<mhynlo@mhynlo.io>
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

# First Party Imports
import sickbeard
from sickbeard import common

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def notify_snatch(self, name):
        if self.config('snatch'):
            self._notify_discord(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + name)

    def notify_download(self, name):
        if self.config('download'):
            self._notify_discord(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + name)

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._notify_discord(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if self.config('update'):
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if self.config('login'):
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ipaddress))

    def notify_postprocess(self, name: str):
        if self.config('process'):
            self._notify_discord(common.notifyStrings[common.NOTIFY_POSTPROCESS] + ': ' + name)

    def test_notify(self):
        return self._notify_discord("This is a test notification from SickChill", force=True)

    @staticmethod
    def _send_discord(message=None, force=False):
        return sickbeard.notificationsTaskScheduler.action.add_item(message, notifier='discord', force_next=force)

    def _notify_discord(self, message='', force=False):
        if not self.config('enabled') and not force:
            return False

        return self._send_discord(message, force=force)
