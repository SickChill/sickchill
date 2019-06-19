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

from __future__ import print_function, unicode_literals

import os
import subprocess

import sickbeard
from sickbeard import common, logger
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import ex


class Notifier(object):
    def notify_snatch(self, ep_name):
        if sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH:
            self._send_synologyNotifier(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD:
            self._send_synologyNotifier(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._send_synologyNotifier(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._send_synologyNotifier(update_text + new_version, title)

    def notify_login(self, ip_address=""):
        if sickbeard.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_synologyNotifier(update_text.format(ip_address), title)

    def _send_synologyNotifier(self, message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        logger.log("Executing command " + str(synodsmnotify_cmd))
        logger.log("Absolute path to command: " + ek(os.path.abspath, synodsmnotify_cmd[0]), logger.DEBUG)
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 cwd=sickbeard.PROG_DIR)
            out, err = p.communicate()  # @UnusedVariable
            logger.log("Script result: " + str(out), logger.DEBUG)
        except OSError as e:
            logger.log("Unable to run synodsmnotify: " + ex(e))
