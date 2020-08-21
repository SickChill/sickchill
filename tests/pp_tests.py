"""
Test post processing
"""

import os.path
import shutil
import unittest

from sickchill import settings
from sickchill.oldbeard.helpers import make_dirs
from sickchill.oldbeard.name_cache import addNameToCache
from sickchill.oldbeard.postProcessor import PostProcessor
from sickchill.tv import TVEpisode, TVShow
from tests import test_lib as test


class PPInitTests(unittest.TestCase):
    """
    Init tests
    """
    def setUp(self):
        """
        Set up tests
        """
        self.post_processor = PostProcessor(test.FILE_PATH)

    def test_init_file_name(self):
        """
        Test file name
        """
        self.assertEqual(self.post_processor.file_name, test.FILENAME)

    def test_init_folder_name(self):
        """
        Test folder name
        """
        self.assertEqual(self.post_processor.folder_name, test.SHOW_NAME)


class PPBasicTests(test.SickChillTestDBCase):
    """
    Basic tests
    """
    def test_process(self):
        """
        Test process
        """
        show = TVShow(1, 3)
        show.name = test.SHOW_NAME
        show.location = test.SHOW_DIR
        show.saveToDB()

        settings.showList = [show]
        episode = TVEpisode(show, test.SEASON, test.EPISODE)
        episode.name = "some episode name"
        episode.saveToDB()

        addNameToCache('show name', 3)
        settings.PROCESS_METHOD = 'move'

        post_processor = PostProcessor(test.FILE_PATH)
        self.assertTrue(post_processor.process())


class ListAssociatedFiles(unittest.TestCase):
    def __init__(self, test_case):
        super().__init__(test_case)
        self.test_tree = os.path.join('Show Name', 'associated_files', 'random', 'recursive', 'subdir')

        file_names = [
            'Show Name [SickChill].avi',
            'Show Name [SickChill].srt',
            'Show Name [SickChill].nfo',
            'Show Name [SickChill].en.srt',
            'Non-Associated Show [SickChill].srt',
            'Non-Associated Show [SickChill].en.srt',
            'Show [SickChill] Non-Associated.en.srt',
            'Show [SickChill] Non-Associated.srt',
        ]
        self.file_list = [os.path.join('Show Name', f) for f in file_names] + [os.path.join(self.test_tree, f) for f in file_names]
        self.post_processor = PostProcessor('Show Name')
        self.maxDiff = None
        settings.MOVE_ASSOCIATED_FILES = True
        settings.ALLOWED_EXTENSIONS = ''

    def setUp(self):
        make_dirs(self.test_tree)
        for test_file in self.file_list:
            open(test_file, 'a').close()

    def tearDown(self):
        shutil.rmtree('Show Name')

    def test_subfolders(self):
        # Test edge cases first:
        self.assertEqual([], # empty file_path
            self.post_processor.list_associated_files('', subfolders=True))
        self.assertEqual([], # no file name
                         self.post_processor.list_associated_files('\\Show Name\\.nomedia', subfolders=True))

        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=True)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list[1:] if 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

        # Test no associated files:
        associated_files = self.post_processor.list_associated_files('Fools Quest.avi', subfolders=True)

    def test_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=False)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list[1:] if 'associated_files' not in file_name and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

    def test_subtitles_only(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=True)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list if file_name.endswith('.srt') and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

    def test_subtitles_only_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=False)
        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list if file_name.endswith('.srt') and 'associated_files' not in file_name and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)


if __name__ == '__main__':
    print("==================")
    print("STARTING - PostProcessor TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(PPInitTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(PPBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ListAssociatedFiles)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
