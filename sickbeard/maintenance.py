# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement
import threading
import sickbeard

from sickbeard import scene_exceptions
from sickbeard import failed_history
from sickbeard import network_timezones


class Maintenance():
    def __init__(self):
        self.lock = threading.Lock()

        self.amActive = False

    def __del__(self):
        pass

    def run(self, force=False):
        self.amActive = True

        # get and update scene exceptions lists
        scene_exceptions.retrieve_exceptions()

        # refresh network timezones
        network_timezones.update_network_dict()

        # sure, why not?
        if sickbeard.USE_FAILED_DOWNLOADS:
            failed_history.trimHistory()

        self.amActive = False