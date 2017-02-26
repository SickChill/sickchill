# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

"""
Test post processing
"""

import os.path
import shutil
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sickbeard
from sickbeard.helpers import make_dirs
from sickbeard.name_cache import addNameToCache
from sickbeard.postProcessor import PostProcessor
from sickbeard.tv import TVEpisode, TVShow

import tests.test_lib as test


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


class PPBasicTests(test.SickbeardTestDBCase):
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

        sickbeard.showList = [show]
        episode = TVEpisode(show, test.SEASON, test.EPISODE)
        episode.name = "some episode name"
        episode.saveToDB()

        addNameToCache('show name', 3)
        sickbeard.PROCESS_METHOD = 'move'

        post_processor = PostProcessor(test.FILE_PATH)
        self.assertTrue(post_processor.process())


class ListAssociatedFiles(unittest.TestCase):
    def __init__(self, test_case):
        super(ListAssociatedFiles, self).__init__(test_case)
        self.test_tree = os.path.join(u'Show Name', u'associated_files', u'random', u'recursive', u'subdir')

        file_names = [
            u'Show Name [SickRage].avi',
            u'Show Name [SickRage].srt',
            u'Show Name [SickRage].nfo',
            u'Show Name [SickRage].en.srt',
            u'Non-Associated Show [SickRage].srt',
            u'Non-Associated Show [SickRage].en.srt',
            u'Show [SickRage] Non-Associated.en.srt',
            u'Show [SickRage] Non-Associated.srt',
        ]
        self.file_list = [os.path.join(u'Show Name', f) for f in file_names] + [os.path.join(self.test_tree, f) for f in file_names]
        self.post_processor = PostProcessor(u'Show Name')
        self.maxDiff = None

    def setUp(self):
        make_dirs(self.test_tree)
        for test_file in self.file_list:
            open(test_file, 'a').close()

    def tearDown(self):
        shutil.rmtree(u'Show Name')

    def test_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=True)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list[1:] if 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

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
