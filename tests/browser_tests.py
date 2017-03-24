# coding=utf-8
"""
Test sickbeard.browser's methods

Methods
    getWinDrives
    getFileList
    foldersAtPath
"""

import logging
import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import browser


class BrowserTestAll(unittest.TestCase):
    """
    Test methods in sickbeard.browser
    """
    def setUp(self):
        self.here = os.path.normpath(os.path.dirname(__file__))

    @unittest.skipUnless(os.name == 'nt', 'Test on Windows only')
    def test_get_win_drives(self):
        """
        Test getWinDrives
        """
        drives = browser.getWinDrives()
        self.assertIsNotNone(drives)
        self.assertIn('C', drives)

    def test_get_file_list(self):
        """
        Test getFileList
        """
        file_list = browser.getFileList(self.here, True, ['py'])
        self.assertIsNotNone(file_list)
        test = file_list[0]
        self.assertTrue('isImage' in test and isinstance(test['isImage'], bool))
        self.assertTrue('isFile' in test and isinstance(test['isImage'], bool))
        self.assertTrue('isAllowed' in test and isinstance(test['isImage'], bool))
        self.assertTrue('name' in test and test['path'].endswith('py'))
        self.assertTrue('path' in test and test['path'].endswith('py'))

    @unittest.skip('Not yet implemented')
    def test_folders_at_path(self):
        """
        Test foldersAtPath
        """
        pass

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(BrowserTestAll)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
