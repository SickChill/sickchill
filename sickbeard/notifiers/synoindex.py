# coding=utf-8

# Author: Sebastien Erard <sebastien_erard@hotmail.com>
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

# Stdlib Imports
import os
import subprocess

# First Party Imports
import sickbeard
from sickbeard import logger
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import ex


class Notifier(object):
    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_git_update(self, new_version):
        pass

    def notify_login(self, ipaddress=""):
        pass

    def moveFolder(self, old_path, new_path):
        self.moveObject(old_path, new_path)

    def moveFile(self, old_file, new_file):
        self.moveObject(old_file, new_file)

    def moveObject(self, old_path, new_path):
        if sickbeard.USE_SYNOINDEX:
            synoindex_cmd = ['/usr/syno/bin/synoindex', '-N', ek(os.path.abspath, new_path),
                             ek(os.path.abspath, old_path)]
            logger.log("Executing command " + str(synoindex_cmd), logger.DEBUG)
            logger.log("Absolute path to command: " + ek(os.path.abspath, synoindex_cmd[0]), logger.DEBUG)
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickbeard.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                logger.log("Script result: " + str(out), logger.DEBUG)
            except OSError as e:
                logger.log("Unable to run synoindex: " + ex(e), logger.ERROR)

    def deleteFolder(self, cur_path):
        self.makeObject('-D', cur_path)

    def addFolder(self, cur_path):
        self.makeObject('-A', cur_path)

    def deleteFile(self, cur_file):
        self.makeObject('-d', cur_file)

    def addFile(self, cur_file):
        self.makeObject('-a', cur_file)

    def makeObject(self, cmd_arg, cur_path):
        if sickbeard.USE_SYNOINDEX:
            synoindex_cmd = ['/usr/syno/bin/synoindex', cmd_arg, ek(os.path.abspath, cur_path)]
            logger.log("Executing command " + str(synoindex_cmd), logger.DEBUG)
            logger.log("Absolute path to command: " + ek(os.path.abspath, synoindex_cmd[0]), logger.DEBUG)
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickbeard.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                logger.log("Script result: " + str(out), logger.DEBUG)
            except OSError as e:
                logger.log("Unable to run synoindex: " + ex(e), logger.ERROR)
