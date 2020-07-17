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
# Stdlib Imports
import os
import subprocess

# First Party Imports
import sickbeard
from sickbeard import logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def __init__(self):
        super().__init__('synoindex')

    def notify_snatch(self, name):
        pass

    def notify_download(self, name):
        pass

    def notify_subtitle_download(self, name, lang):
        pass

    def notify_git_update(self, new_version):
        pass

    def notify_login(self, ipaddress=""):
        pass

    def notify_postprocess(self, name: str):
        pass

    @staticmethod
    def test_notify(username):
        pass

    def update_library(self, item, remove: bool = False):
        if not isinstance(item, str):
            item = item._location
        if remove:
            self.deleteFile(item)
        else:
            self.addFile(item)

    def moveFolder(self, old_path, new_path):
        self.__move(old_path, new_path)

    def moveFile(self, old_file, new_file):
        self.__move(old_file, new_file)

    def __move(self, old_path, new_path):
        self.__call_script(
            command=['/usr/syno/bin/synoindex', '-N', os.path.abspath(new_path), os.path.abspath(old_path)]
        )

    def deleteFolder(self, path):
        self.__call_script('-D', path)

    def addFolder(self, path):
        self.__call_script('-A', path)

    def deleteFile(self, path):
        self.__call_script('-d', path)

    def addFile(self, path):
        self.__call_script('-a', path)

    def __call_script(self, cmd_arg: str = "", path: str = "", command: list = None):
        if self.config('enabled'):
            if command:
                synoindex_cmd = command
            else:
                synoindex_cmd = ['/usr/syno/bin/synoindex', cmd_arg, os.path.abspath(path)]

            logger.debug("Executing command " + str(synoindex_cmd))
            logger.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickbeard.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                logger.debug("Script result: " + str(out))
            except OSError as e:
                logger.exception("Unable to run synoindex: " + str(e))
