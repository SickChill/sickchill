# coding=UTF-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

"""
Test the post processor queue
"""

import datetime
import os.path
import sys
import time
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tests.test_lib as test
import sickbeard
from sickbeard.post_processing_queue import ProcessingQueue, PostProcessorTask

CHECK_CLEARS = False


class PostProcessorQueueTests(test.SickbeardTestPostProcessorCase):
    """
    Test the post processor queue
    """

    def __init__(self, testCaseNames):
        super(PostProcessorQueueTests, self).__init__(testCaseNames)
        self.queue = None

    def setUp(self):
        super(PostProcessorQueueTests, self).setUp()
        self.queue = sickbeard.scheduler.Scheduler(
            ProcessingQueue(),
            run_delay=datetime.timedelta(seconds=0),
            cycleTime=datetime.timedelta(seconds=1),
            threadName="POSTPROCESSOR",
        )
        self.queue.enable = True
        self.queue.start()

    def tearDown(self):
        self.queue.stop.set()
        super(PostProcessorQueueTests, self).tearDown()

    def test_post_processor_queue_spam(self):
        for i in range(100):
            result = self.queue.action.add_item(sickbeard.TV_DOWNLOAD_DIR, method='move', mode=('manual', 'auto')[i % 2])
            self.assertIsNotNone(result)
            self.assertTrue(self.queue.action.queue_length()['auto'] <= 1)
            self.assertTrue(self.queue.action.queue_length()['manual'] <= 1)
            self.assertTrue(len(self.queue.action.queue) <= 2)

        for task in self.queue.action.queue:
            self.assertIsInstance(task, PostProcessorTask)

        if CHECK_CLEARS:
            cleared = False
            timeout = 300
            for i in range(timeout):
                if not len(self.queue.action.queue):
                    cleared = True
                    break
                time.sleep(1)

            print(self.queue.action.queue)
            if cleared:
                print('cleared after {}'.format(i))
            for task in self.queue.action.queue:
                print(task.last_result)

            self.assertTrue(cleared, 'The queue did not empty after {timeout} seconds'.format(timeout=timeout))



if __name__ == "__main__":
    print ("==================")
    print ("STARTING - Post Processor Queue TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PostProcessorQueueTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
