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

import datetime
import time
import threading
import traceback

from sickbeard import logger
from sickbeard.exceptions import ex


class Scheduler(threading.Thread):
    def __init__(self, action, cycleTime=datetime.timedelta(minutes=10), run_delay=datetime.timedelta(minutes=0),
                 start_time=None, threadName="ScheduledThread", silent=True):
        super(Scheduler, self).__init__()

        self.lastRun = datetime.datetime.now() + run_delay - cycleTime
        self.action = action
        self.cycleTime = cycleTime
        self.start_time = start_time

        self.name = threadName
        self.silent = silent
        self.stop = threading.Event()
        self.force = False

    def timeLeft(self):
        return self.cycleTime - (datetime.datetime.now() - self.lastRun)

    def forceRun(self):
        if not self.action.amActive:
            self.lastRun = datetime.datetime.fromordinal(1)
            self.force = True
            return True
        return False

    def run(self):
        try:
            while not self.stop.is_set():

                current_time = datetime.datetime.now()
                should_run = False

                # check if interval has passed
                if current_time - self.lastRun >= self.cycleTime:
                    # check if wanting to start around certain time taking interval into account
                    if self.start_time:
                        hour_diff = current_time.time().hour - self.start_time.hour
                        if not hour_diff < 0 and hour_diff < self.cycleTime.seconds / 3600:
                            should_run = True
                        else:
                            # set lastRun to only check start_time after another cycleTime
                            self.lastRun = current_time
                    else:
                        should_run = True

                if should_run:
                    self.lastRun = current_time

                    if not self.silent:
                        logger.log(u"Starting new thread: " + self.name, logger.DEBUG)

                    self.action.run(self.force)

                if self.force:
                    self.force = False

                time.sleep(1)

            # exiting thread
            self.stop.clear()
        except Exception, e:
            logger.log(u"Exception generated in thread " + self.name + ": " + ex(e), logger.ERROR)
            logger.log(repr(traceback.format_exc()), logger.DEBUG)