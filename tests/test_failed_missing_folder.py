"""Regression: a failed download whose folder no longer exists must still be processed as failed.

NZBGet's health check can delete a job before anything is written, then report it as failed
for a folder that was never created. process_dir used to return at the folder check, so the
failure was never recorded and no other release was searched for.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from sickchill.oldbeard import processTV
from sickchill.views.api.webapi import CMDPostProcess


class FailedMissingFolderTests(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.mkdtemp()
        self.release = "Show.Name.S01E01.720p.HDTV.x264-GROUP"
        # NZBGet appends .#<id> to the intermediate folder name
        self.missing = os.path.join(self.parent, self.release + ".#8585")

    def tearDown(self):
        os.rmdir(self.parent)

    @patch("sickchill.oldbeard.processTV.process_failed")
    def test_failed_missing_folder_uses_folder_name(self, process_failed):
        processTV.process_dir(self.missing, failed=True)
        process_failed.assert_called_once()
        self.assertEqual(process_failed.call_args.args[:2], (self.missing, self.release))

    @patch("sickchill.oldbeard.processTV.process_failed")
    def test_failed_missing_folder_prefers_release_name(self, process_failed):
        processTV.process_dir(self.missing, release_name="Other.Name.S01E02.1080p.WEB-GRP", failed=True)
        self.assertEqual(process_failed.call_args.args[1], "Other.Name.S01E02.1080p.WEB-GRP")

    @patch("sickchill.oldbeard.processTV.process_failed")
    def test_not_failed_missing_folder_is_skipped(self, process_failed):
        output = processTV.process_dir(self.missing, failed=False)
        process_failed.assert_not_called()
        self.assertIn("Unable to figure out what folder to process", output)


class PostProcessApiFallbackTests(unittest.TestCase):
    def test_nzbname_is_used_as_release_name(self):
        command = CMDPostProcess([], {"path": "/downloads/x", "nzbName": "Show.Name.S01E01.720p.HDTV.x264-GROUP", "failed": "1"})
        self.assertEqual(command.release_name, "Show.Name.S01E01.720p.HDTV.x264-GROUP")

    def test_release_name_wins_over_nzbname(self):
        command = CMDPostProcess([], {"path": "/downloads/x", "nzbName": "old", "release_name": "new"})
        self.assertEqual(command.release_name, "new")

    def test_proc_dir_is_used_as_path(self):
        command = CMDPostProcess([], {"proc_dir": "/downloads/y"})
        self.assertEqual(command.path, "/downloads/y")

    def test_force_and_quiet_fallbacks(self):
        command = CMDPostProcess([], {"path": "/downloads/x", "force": "1", "quiet": "1"})
        self.assertTrue(command.force_replace)
        self.assertTrue(command.return_data)

    def test_explicit_false_wins_over_deprecated_alias(self):
        command = CMDPostProcess([], {"path": "/downloads/x", "force_replace": "0", "force": "1", "return_data": "0", "quiet": "1"})
        self.assertFalse(command.force_replace)
        self.assertFalse(command.return_data)


if __name__ == "__main__":
    unittest.main()
