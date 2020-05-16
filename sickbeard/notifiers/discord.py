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

from __future__ import absolute_import, print_function, unicode_literals

# First Party Imports
import sickbeard
from sickbeard import common


class Notifier(object):

    def notify_snatch(self, ep_name):
        if sickbeard.DISCORD_NOTIFY_SNATCH:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.DISCORD_NOTIFY_DOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.DISCORD_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_discord("This is a test notification from SickChill", force=True)

    @staticmethod
    def _send_discord(message=None, force=False):
        return sickbeard.notificationsTaskScheduler.action.add_item(message, notifier='discord', force_next=force)

    def _notify_discord(self, message='', force=False):
        if not sickbeard.USE_DISCORD and not force:
            return False

        return self._send_discord(message, force=force)
