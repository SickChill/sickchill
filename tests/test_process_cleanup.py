"""Move-mode cleanup must not delete a failed input or the target of a directory symlink."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sickchill.process import processTV


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

        def walk(path, followlinks=False):
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
