# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import threading

import sickbeard


class PostProcessor(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the postprocessor

        :param force: Forces postprocessing run
        :return: Returns when done without a return state/code
        """
        self.amActive = True
        sickbeard.postProcessorTaskScheduler.action.add_item(sickbeard.TV_DOWNLOAD_DIR, force=force)
        self.amActive = False

    def __del__(self):
        pass
