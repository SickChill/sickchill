# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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
import threading

from sickbeard import logger


class QueuePriorities:
    LOW = 10
    NORMAL = 20
    HIGH = 30


class GenericQueue(object):
    def __init__(self):

        self.currentItem = None

        self.queue = []

        self.queue_name = "QUEUE"

        self.min_priority = 0

        self.lock = threading.Lock()

    def pause(self):
        """Pauses this queue"""
        logger.log(u"Pausing queue")
        self.min_priority = 999999999999

    def unpause(self):
        """Unpauses this queue"""
        logger.log(u"Unpausing queue")
        self.min_priority = 0

    def add_item(self, item):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :return: item
        """
        with self.lock:
            item.added = datetime.datetime.now()
            self.queue.append(item)

            return item

    def run(self, force=False):
        """
        Process items in this queue

        :param force: Force queue processing (currently not implemented)
        """
        with self.lock:
            # only start a new task if one isn't already going
            if self.currentItem is None or not self.currentItem.isAlive():

                # if the thread is dead then the current item should be finished
                if self.currentItem:
                    self.currentItem.finish()
                    self.currentItem = None

                # if there's something in the queue then run it in a thread and take it out of the queue
                if len(self.queue) > 0:

                    # sort by priority
                    def sorter(x, y):
                        """
                        Sorts by priority descending then time ascending
                        """
                        if x.priority == y.priority:
                            if y.added == x.added:
                                return 0
                            elif y.added < x.added:
                                return 1
                            elif y.added > x.added:
                                return -1
                        else:
                            return y.priority - x.priority

                    self.queue.sort(cmp=sorter)
                    if self.queue[0].priority < self.min_priority:
                        return

                    # launch the queue item in a thread
                    self.currentItem = self.queue.pop(0)
                    self.currentItem.name = self.queue_name + '-' + self.currentItem.name
                    self.currentItem.start()

        self.amActive = False

class QueueItem(threading.Thread):
    def __init__(self, name, action_id=0):
        super(QueueItem, self).__init__()

        self.name = name.replace(" ", "-").upper()
        self.inProgress = False
        self.priority = QueuePriorities.NORMAL
        self.action_id = action_id
        self.stop = threading.Event()
        self.added = None

    def run(self):
        """Implementing classes should call this"""

        self.inProgress = True

    def finish(self):
        """Implementing Classes should call this"""

        self.inProgress = False

        threading.currentThread().name = self.name
