import logging
import os
import string
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
        self.assertIn(f"{Path.cwd().drive}{os.sep}", drives, f"Drives[{drives}]")

    def test_folders_at_path(self):
        """
        Test foldersAtPath
        """
        test_list = browser.folders_at_path(self.here / "not_a_real_path")
        assert test_list[0]["currentPath"] == str(self.here.parent)

        test_list = browser.folders_at_path(Path("//"))
        if os.name == "nt":
            assert test_list[0]["currentPath"] == "My Computer", test_list[0]
            drives = browser.get_windows_drives()
            assert len(drives)
            assert len(test_list[1:])
            for item in test_list[1:]:
                if item["path"].upper()[0] in string.ascii_uppercase:
                    assert item["path"][:3] in drives, (item["path"], drives)
        else:
            assert test_list[0]["currentPath"] == "/"

        test_list = browser.folders_at_path(self.here, include_parent=True)
        assert test_list[0]["currentPath"] == str(self.here.parent)
        assert test_list[1]["name"] == ".."
        assert test_list[1]["path"] == str(self.here.parent.parent)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(BrowserTestAll)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
