import logging
import os
import sys
import unittest

from sickchill.oldbeard import browser


class BrowserTestAll(unittest.TestCase):
    """
    Test methods in oldbeard.browser
    """

    def setUp(self):
        self.here = os.path.normpath(os.path.dirname(__file__))

    @unittest.skipUnless(os.name == "nt", "Test on Windows only")
    def test_get_win_drives(self):
        """
        Test getWinDrives
        """
        drives = browser.getWinDrives()
        self.assertIsNotNone(drives)
        self.assertIn("C", drives)

    def test_get_file_list(self):
        """
        Test getFileList
        """
        file_list = browser.getFileList(self.here, True, ["py", "images"])
        self.assertIsNotNone(file_list)
        for entry in file_list:
            assert "name" in entry
            assert "path" in entry
            assert "isImage" in entry
            assert "isFile" in entry
            assert "isAllowed" in entry

            if entry["name"].endswith((".jpg", ".jpeg", ".png", ".tiff", ".gif")):
                assert entry["isImage"]
            else:
                assert not entry["isImage"]

            if entry["name"].endswith(".py") or entry["isImage"]:
                assert entry["isFile"]
            else:
                assert not entry["isFile"]
            assert entry["isAllowed"]

        # folders only
        file_list = browser.getFileList(self.here, False, [])
        self.assertIsNotNone(file_list)
        for entry in file_list:
            assert "name" in entry
            assert "path" in entry
            assert "isImage" in entry
            assert "isFile" in entry
            assert "isAllowed" in entry

            assert not entry["isImage"]
            assert not entry["isFile"]
            assert entry["isAllowed"]

    def test_folders_at_path(self):
        """
        Test foldersAtPath
        """
        test_list = browser.foldersAtPath(os.path.join(self.here, "not_a_real_path"))
        assert test_list[0]["currentPath"] == self.here

        test_list = browser.foldersAtPath("")
        if os.name == "nt":
            assert test_list[0]["currentPath"] == "Root"
            drives = browser.getWinDrives()
            assert len(drives) == len(test_list[1:])
            for item in test_list[1:]:
                assert item["path"].strip(":\\") in drives
        else:
            assert test_list[0]["currentPath"] == "/"

        test_list = browser.foldersAtPath(os.path.join(self.here), includeParent=True)
        assert test_list[0]["currentPath"] == self.here
        assert test_list[1]["name"] == ".."
        assert test_list[1]["path"] == os.path.dirname(self.here)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(BrowserTestAll)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
