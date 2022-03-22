"""
Test post processing
"""

import shutil
import unittest
from pathlib import Path

from sickchill import settings
from sickchill.oldbeard.name_cache import add_name
from sickchill.oldbeard.postProcessor import PostProcessor
from sickchill.tv import TVEpisode, TVShow
from tests import conftest


class PPInitTests(unittest.TestCase):
    """
    Init tests
    """

    def setUp(self):
        """
        Set up tests
        """
        self.post_processor = PostProcessor(conftest.FILE_PATH)

    def test_init_filename(self):
        """
        Test file name
        """
        assert self.post_processor.filename == conftest.FILENAME

    def test_init_folder_name(self):
        """
        Test folder name
        """
        assert self.post_processor.folder_name == conftest.SHOW_NAME


class PPBasicTests(conftest.SickChillTestDBCase):
    """
    Basic tests
    """

    def test_process(self):
        """
        Test process
        """
        show = TVShow(1, 3)
        show.name = conftest.SHOW_NAME
        show.location = conftest.SHOW_DIR
        show.saveToDB()

        settings.showList = [show]
        episode = TVEpisode(show, conftest.SEASON, conftest.EPISODE)
        episode.name = "some episode name"
        episode.saveToDB()

        add_name("show name", 3)
        settings.PROCESS_METHOD = "move"

        post_processor = PostProcessor(conftest.FILE_PATH)
        assert post_processor.process()


class ListAssociatedFiles(unittest.TestCase):
    def __init__(self, test_case):
        super().__init__(test_case)
        self.test_tree = Path("Show Name") / "associated_files" / "random" / "recursive" / "subdir"

        filenames = [
            "Show Name [SickChill].avi",
            "Show Name [SickChill].srt",
            "Show Name [SickChill].nfo",
            "Show Name [SickChill].en.srt",
            "Non-Associated Show [SickChill].srt",
            "Non-Associated Show [SickChill].en.srt",
            "Show [SickChill] Non-Associated.en.srt",
            "Show [SickChill] Non-Associated.srt",
        ]
        self.file_list = [(Path("Show Name") / f).resolve() for f in filenames] + [(self.test_tree / f) for f in filenames]
        self.post_processor = PostProcessor(Path("Show Name"))
        self.maxDiff = None
        settings.MOVE_ASSOCIATED_FILES = True
        settings.ALLOWED_EXTENSIONS = ""

    def setUp(self):
        self.test_tree.mkdir(parents=True, exist_ok=True)
        for test_file in self.file_list:
            open(test_file, "a").close()

    def tearDown(self):
        shutil.rmtree("Show Name")

    def test_subfolders(self):
        # Test edge cases first:
        assert self.post_processor.list_associated_files(Path(""), subfolders=True) == []  # empty file_path
        assert self.post_processor.list_associated_files(Path("\\Show Name\\.nomedia"), subfolders=True) == []  # no file name

        associated_files = sorted(self.post_processor.list_associated_files(self.file_list[0], subfolders=True))
        out_list = sorted(filename for filename in self.file_list[1:] if "Non-Associated" not in filename.__fspath__())
        assert associated_files == out_list

        # Test no associated files:
        associated_files = self.post_processor.list_associated_files(Path("Fools Quest.avi"), subfolders=True)
        assert associated_files == []

    def test_no_subfolders(self):
        associated_files = sorted(self.post_processor.list_associated_files(self.file_list[0], subfolders=False))
        out_list = sorted(filename for filename in self.file_list[1:] if "associated_files" not in filename.__fspath__() and "Non-Associated" not in filename.__fspath__())

        assert associated_files == out_list

    def test_subtitles_only(self):
        associated_files = sorted(self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=True))
        out_list = sorted(filename for filename in self.file_list if filename.suffix == ".srt" and "Non-Associated" not in filename.__fspath__())

        assert associated_files == out_list

    def test_subtitles_only_no_subfolders(self):
        associated_files = sorted(self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=False))
        out_list = sorted(
            filename for filename in self.file_list if filename.suffix == ".srt" and "associated_files" not in filename.__fspath__() and "Non-Associated" not in filename.__fspath__()
        )

        assert associated_files == out_list


if __name__ == "__main__":
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
