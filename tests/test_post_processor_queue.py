"""
Test the post processor queue
"""

import datetime
import os
import os.path
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sickchill
from sickchill import settings
from sickchill.process import processTV
from sickchill.process.post_processing_queue import PostProcessorTask, ProcessingQueue
from tests import conftest

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
        self.queue = sickchill.helper.scheduler.Scheduler(
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


def _processor(path, _release_name, _process_method, _is_priority, fail_name="a.mkv"):
    processor = MagicMock()
    processor.log = ""
    processor.show = None
    failed = os.path.basename(path) == fail_name
    processor.process.return_value = not failed
    processor.failure_reason = "failed" if failed else ""
    return processor


class DeleteFolderSymlinkTests(unittest.TestCase):
    def test_directory_symlink_is_not_removed(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        target = Path(root) / "library"
        target.mkdir()
        kept = target / "keep.txt"
        kept.write_text("safe")
        link = Path(root) / "@eaDir"
        link.symlink_to(target, target_is_directory=True)

        self.assertFalse(processTV.delete_folder(link, check_empty=False))
        self.assertTrue(link.is_symlink())
        self.assertEqual(kept.read_text(), "safe")

    def test_real_directory_is_removed(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        folder = Path(root) / "download"
        folder.mkdir()
        (folder / "gone.txt").write_text("x")

        self.assertTrue(processTV.delete_folder(folder, check_empty=False))
        self.assertFalse(folder.exists())


class MoveCleanupTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.folder = Path(self.root) / "job"
        self.folder.mkdir()

    def _video(self, name):
        path = self.folder / name
        path.write_bytes(b"video")
        return path

    def _run(self, fail_name, filenames=None):
        def factory(path, release_name, process_method, is_priority):
            return _processor(path, release_name, process_method, is_priority, fail_name=fail_name)

        # Windows shutil.rmtree walks with topdown=False. Keep that on the real walk.
        real_walk = os.walk

        def walk(path, topdown=True, onerror=None, followlinks=False):
            if not topdown or onerror is not None:
                yield from real_walk(path, topdown=topdown, onerror=onerror, followlinks=followlinks)
                return
            yield str(path), [], list(filenames or ["a.mkv", "b.mkv"])

        with (
            patch("sickchill.process.processTV.validate_dir", return_value=True),
            patch("sickchill.process.processTV.already_processed", return_value=False),
            patch("sickchill.process.processTV.os.walk", side_effect=walk),
            patch("sickchill.process.processTV.postProcessor.PostProcessor", side_effect=factory),
        ):
            processTV.process_dir(str(self.folder), process_method="move", delete_on=True, mode="auto")

    def test_failed_video_is_kept_when_a_later_video_succeeds(self):
        failed = self._video("a.mkv")
        succeeded = self._video("b.mkv")
        eadir = self.folder / "@eaDir"
        eadir.mkdir()
        (eadir / "meta").write_text("thumb")

        # Failure first, then success. result.result used to keep only the success and delete both sources.
        self._run(fail_name="a.mkv", filenames=["a.mkv", "b.mkv"])

        self.assertTrue(failed.is_file())
        self.assertFalse(succeeded.exists())
        self.assertTrue(eadir.is_dir())
        self.assertTrue((eadir / "meta").is_file())
        self.assertTrue(self.folder.is_dir())

    def test_successful_folder_still_cleans_a_real_eadir(self):
        self._video("a.mkv")
        self._video("b.mkv")
        eadir = self.folder / "@eaDir"
        eadir.mkdir()
        (eadir / "meta").write_text("thumb")

        self._run(fail_name="")

        self.assertFalse(self.folder.exists())

    def test_successful_folder_does_not_follow_eadir_symlink(self):
        self._video("a.mkv")
        self._video("b.mkv")
        target = Path(self.root) / "library"
        target.mkdir()
        kept = target / "keep.txt"
        kept.write_text("safe")
        link = self.folder / "@eaDir"
        link.symlink_to(target, target_is_directory=True)

        self._run(fail_name="")

        self.assertEqual(kept.read_text(), "safe")
        self.assertTrue(target.is_dir())


if __name__ == "__main__":
    print("==================")
    print("STARTING - Post Processor Queue TESTS")
    print("==================")
    print("######################################################################")
    loader = unittest.TestLoader()
    SUITE = unittest.TestSuite(
        [
            loader.loadTestsFromTestCase(PostProcessorQueueTests),
            loader.loadTestsFromTestCase(DeleteFolderSymlinkTests),
            loader.loadTestsFromTestCase(MoveCleanupTests),
        ]
    )
    unittest.TextTestRunner(verbosity=2).run(SUITE)
