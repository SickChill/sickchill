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
        file_list = browser.getFileList(self.here, True, ['py', 'images'])
        self.assertIsNotNone(file_list)
        for entry in file_list:
            self.assertTrue('name' in entry)
            self.assertTrue('path' in entry)
            self.assertTrue('isImage' in entry)
            self.assertTrue('isFile' in entry)
            self.assertTrue('isAllowed' in entry)

            if entry['name'].endswith(('.jpg', '.jpeg', '.png', '.tiff', '.gif')):
                self.assertTrue(entry['isImage'])
            else:
                self.assertFalse(entry['isImage'])

            if entry['name'].endswith('.py') or entry['isImage']:
                self.assertTrue(entry['isFile'])
            else:
                self.assertFalse(entry['isFile'])
            self.assertTrue(entry['isAllowed'])

        # folders only
        file_list = browser.getFileList(self.here, False, [])
        self.assertIsNotNone(file_list)
        for entry in file_list:
            self.assertTrue('name' in entry)
            self.assertTrue('path' in entry)
            self.assertTrue('isImage' in entry)
            self.assertTrue('isFile' in entry)
            self.assertTrue('isAllowed' in entry)

            self.assertFalse(entry['isImage'])
            self.assertFalse(entry['isFile'])
            self.assertTrue(entry['isAllowed'])

    def test_folders_at_path(self):
        """
        Test foldersAtPath
        """
        test_list = browser.foldersAtPath(os.path.join(self.here, 'not_a_real_path'))
        self.assertEqual(test_list[0]['currentPath'], self.here)

        test_list = browser.foldersAtPath('')
        if os.name == 'nt':
            self.assertEqual(test_list[0]['currentPath'], 'Root')
            drives = browser.getWinDrives()
            self.assertEqual(len(drives), len(test_list[1:]))
            for item in test_list[1:]:
                self.assertTrue(item['path'].strip(':\\') in drives)
        else:
            self.assertEqual(test_list[0]['currentPath'], '/')

        test_list = browser.foldersAtPath(os.path.join(self.here), includeParent=True)
        self.assertEqual(test_list[0]['currentPath'], self.here)
        self.assertEqual(test_list[1]['name'], '..')
        self.assertEqual(test_list[1]['path'], os.path.dirname(self.here))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(BrowserTestAll)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
