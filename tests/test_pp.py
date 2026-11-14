"""
Test post processing
"""

import os.path
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sickchill import settings
from sickchill.helper.exceptions import EpisodeNotFoundException, EpisodePostProcessingFailedException
from sickchill.oldbeard import processTV
from sickchill.oldbeard.helpers import make_dirs
from sickchill.oldbeard.name_cache import add_name
from sickchill.oldbeard.postProcessor import METHOD_COPY, METHOD_HARDLINK, METHOD_MOVE, METHOD_SYMLINK, METHOD_SYMLINK_REVERSED, PostProcessor
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
        show.save_to_db()

        settings.show_list = [show]
        episode = TVEpisode(show, conftest.SEASON, conftest.EPISODE)
        episode.name = "some episode name"
        episode.save_to_db()

        add_name("show name", 3)
        settings.PROCESS_METHOD = "move"

        post_processor = PostProcessor(conftest.FILE_PATH)
        assert post_processor.process()


class PPMultiEpFailureMessageTests(unittest.TestCase):
    """Multi-ep (3 shorts in one file) must not fail with an empty reason."""

    def test_get_ep_obj_missing_third_episode_message(self):
        show = MagicMock()

        def get_episode(season, episode):
            if episode == 18:
                raise EpisodeNotFoundException("Couldn't find episode S{0:02d}E{1:02d}".format(season, episode))
            ep = MagicMock()
            ep.season = season
            ep.episode = episode
            return ep

        show.get_episode.side_effect = get_episode
        post_processor = PostProcessor("/tmp/Puffin.Rock.S02E16e17e18.mkv")

        with self.assertRaises(EpisodePostProcessingFailedException) as ctx:
            post_processor._get_ep_obj(show, 2, [16, 17, 18])

        message = str(ctx.exception)
        self.assertTrue(message.strip(), "failure exception must include a reason")
        self.assertIn("S02E18", message)
        self.assertIn("S02E16", message)
        self.assertIn("multi-ep", message.lower())

    def test_process_media_surfaces_failure_reason_on_false(self):
        result = processTV.ProcessResult()
        processor = MagicMock()
        processor.process.return_value = False
        processor.failure_reason = "File exists and new file quality is not in a preferred quality list"
        processor.log = "processor log line\n"
        video_name = "Show.S02E16e17e18.mkv"
        process_path = os.path.join(os.path.sep, "tmp")
        video_path = os.path.join(process_path, video_name)

        with patch("sickchill.oldbeard.processTV.postProcessor.PostProcessor", return_value=processor):
            with patch("sickchill.oldbeard.processTV.already_processed", return_value=False):
                processTV.process_media(process_path, [video_name], None, "move", False, False, result)

        self.assertFalse(result.result)
        self.assertIn(processor.failure_reason, result.output)
        # Empty reason after colon must not appear; path join is OS-specific (\ vs /).
        self.assertNotIn(f"Processing failed for {video_path}:\n", result.output)
        self.assertIn(f"Processing failed for {video_path}: {processor.failure_reason}", result.output)

    def test_fail_helper_sets_failure_reason(self):
        post_processor = PostProcessor("/tmp/missing.mkv")
        self.assertFalse(post_processor._fail("did unrar fail?"))
        self.assertEqual(post_processor.failure_reason, "did unrar fail?")


class ListAssociatedFiles(unittest.TestCase):
    def __init__(self, test_case):
        super().__init__(test_case)
        self.test_tree = os.path.join("Show Name", "associated_files", "random", "recursive", "subdir")

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
        self.file_list = [os.path.join("Show Name", f) for f in filenames] + [os.path.join(self.test_tree, f) for f in filenames]
        self.post_processor = PostProcessor("Show Name")
        self.maxDiff = None
        settings.MOVE_ASSOCIATED_FILES = True
        settings.ALLOWED_EXTENSIONS = ""

    def setUp(self):
        make_dirs(self.test_tree)
        for test_file in self.file_list:
            open(test_file, "a").close()

    def tearDown(self):
        shutil.rmtree("Show Name")

    def test_subfolders(self):
        # Test edge cases first:
        assert self.post_processor.list_associated_files("", subfolders=True) == []  # empty file_path
        assert self.post_processor.list_associated_files("\\Show Name\\.nomedia", subfolders=True) == []  # no file name

        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=True)

        associated_files = sorted(filename.lstrip("./") for filename in associated_files)
        out_list = sorted(filename for filename in self.file_list[1:] if "Non-Associated" not in filename)

        assert associated_files == out_list

        # Test no associated files:
        associated_files = self.post_processor.list_associated_files("Fools Quest.avi", subfolders=True)

    def test_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=False)

        associated_files = sorted(filename.lstrip("./") for filename in associated_files)
        out_list = sorted(filename for filename in self.file_list[1:] if "associated_files" not in filename and "Non-Associated" not in filename)

        assert associated_files == out_list

    def test_subtitles_only(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=True)

        associated_files = sorted(filename.lstrip("./") for filename in associated_files)
        out_list = sorted(filename for filename in self.file_list if filename.endswith(".srt") and "Non-Associated" not in filename)

        assert associated_files == out_list

    def test_subtitles_only_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True, subfolders=False)
        associated_files = sorted(filename.lstrip("./") for filename in associated_files)
        out_list = sorted(
            filename for filename in self.file_list if filename.endswith(".srt") and "associated_files" not in filename and "Non-Associated" not in filename
        )

        assert associated_files == out_list


class SourcePreservingAssociatedFiles(unittest.TestCase):
    """Copy/hardlink/symlink_reversed must not delete source associated files such as .nfo."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.src_dir = Path(self.tmpdir) / "src"
        self.dest_dir = Path(self.tmpdir) / "dest"
        self.src_dir.mkdir()
        self.dest_dir.mkdir()
        self.video = self.src_dir / "Show.S01E01.mkv"
        self.nfo = self.src_dir / "Show.S01E01.nfo"
        self.video.write_bytes(b"video")
        self.nfo.write_text("nfo")

        self._move_associated = settings.MOVE_ASSOCIATED_FILES
        self._delete_non = settings.DELETE_NON_ASSOCIATED_FILES
        self._allowed = settings.ALLOWED_EXTENSIONS
        self.addCleanup(self._restore_settings)
        settings.DELETE_NON_ASSOCIATED_FILES = True
        settings.MOVE_ASSOCIATED_FILES = False
        settings.ALLOWED_EXTENSIONS = "srt,ass,ssa,nfo,srr,sfv"

    def _restore_settings(self):
        settings.MOVE_ASSOCIATED_FILES = self._move_associated
        settings.DELETE_NON_ASSOCIATED_FILES = self._delete_non
        settings.ALLOWED_EXTENSIONS = self._allowed

    def _process(self, method):
        processor = PostProcessor(str(self.video), process_method=method)
        with patch("sickchill.oldbeard.helpers.chmodAsParent"):
            if method == METHOD_COPY:
                processor._copy(str(self.video), str(self.dest_dir), None, associated_files=True)
            elif method == METHOD_HARDLINK:
                processor._hardlink(str(self.video), str(self.dest_dir), None, associated_files=True)
            elif method == METHOD_SYMLINK_REVERSED:
                processor._symlink(str(self.video), str(self.dest_dir), None, associated_files=True)
            elif method == METHOD_MOVE:
                processor._move(str(self.video), str(self.dest_dir), None, associated_files=True)
            elif method == METHOD_SYMLINK:
                processor._move_and_symlink(str(self.video), str(self.dest_dir), None, associated_files=True)

    def test_copy_keeps_source_nfo(self):
        self._process(METHOD_COPY)
        self.assertTrue(self.nfo.is_file())
        self.assertTrue(self.video.is_file())

    def test_hardlink_keeps_source_nfo(self):
        self._process(METHOD_HARDLINK)
        self.assertTrue(self.nfo.is_file())
        self.assertTrue(self.video.is_file())

    def test_symlink_reversed_keeps_source_nfo(self):
        self._process(METHOD_SYMLINK_REVERSED)
        self.assertTrue(self.nfo.is_file())
        self.assertTrue(self.video.is_file())

    def test_move_still_deletes_disallowed_source_nfo_when_not_moving_associated(self):
        settings.MOVE_ASSOCIATED_FILES = False
        self._process(METHOD_MOVE)
        self.assertFalse(self.nfo.exists())


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
