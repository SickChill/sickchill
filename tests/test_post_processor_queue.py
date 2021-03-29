"""
Test the post processor queue
"""
import datetime
import os.path
import time
import unittest

from tests import conftest

import sickchill.oldbeard
from sickchill import settings
from sickchill.oldbeard.post_processing_queue import PostProcessorTask, ProcessingQueue

CHECK_CLEARS = False


class PostProcessorQueueTests(conftest.SickChillTestPostProcessorCase):
    """
    Test the post processor queue
    """

    def __init__(self, testCaseNames):
        super().__init__(testCaseNames)
        self.queue = None

    def setUp(self):
        super().setUp()
        self.queue = sickchill.oldbeard.scheduler.Scheduler(
            ProcessingQueue(),
            run_delay=datetime.timedelta(seconds=0),
            cycleTime=datetime.timedelta(seconds=1),
            threadName="POSTPROCESSOR",
        )
        self.queue.enable = True
        self.queue.start()

    def tearDown(self):
        self.queue.stop.set()
        super().tearDown()

    def test_post_processor_queue_spam(self):
        settings.TV_DOWNLOAD_DIR = os.path.abspath(".")
        for i in range(100):
            result = self.queue.action.add_item(settings.TV_DOWNLOAD_DIR, method="move", mode=("manual", "auto")[i % 2])
            self.assertIsNotNone(result)
            assert self.queue.action.queue_length()["auto"] <= 1
            assert self.queue.action.queue_length()["manual"] <= 1
            assert len(self.queue.action.queue) <= 2

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
                print("cleared after {}".format(i))
            for task in self.queue.action.queue:
                print(task.last_result)

            assert cleared, "The queue did not empty after {timeout} seconds".format(timeout=timeout)


if __name__ == "__main__":
    print("==================")
    print("STARTING - Post Processor Queue TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PostProcessorQueueTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
