import logging
import os
import sys
import unittest
from pathlib import Path

from sickchill.oldbeard import browser


class BrowserTestAll(unittest.TestCase):
    """
    Test methods in `oldbeard.browser`
    """

    def setUp(self):
        self.here = Path(__file__)

    @unittest.skipUnless(os.name == "nt", "Test on Windows only")
    def test_get_win_drives(self):
        """
        Test getWinDrives
        """
        drives = browser.get_windows_drives()
        self.assertIsNotNone(drives)
        self.assertIn("C", drives)

    def test_folders_at_path(self):
        """
        Test foldersAtPath
        """
        test_list = browser.folders_at_path(self.here / "not_a_real_path")
        assert test_list[0]["currentPath"] == self.here

        test_list = browser.folders_at_path(Path(""))
        if os.name == "nt":
            assert test_list[0]["currentPath"] == "Root"
            drives = browser.get_windows_drives()
            assert len(drives) == len(test_list[1:])
            for item in test_list[1:]:
                assert item["path"].strip(":\\") in drives
        else:
            assert test_list[0]["currentPath"] == "/"

        test_list = browser.folders_at_path(self.here, include_parent=True)
        assert test_list[0]["currentPath"] == self.here
        assert test_list[1]["name"] == ".."
        assert test_list[1]["path"] == os.path.dirname(self.here)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(BrowserTestAll)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
