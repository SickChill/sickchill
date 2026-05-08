"""Tests for subtitle scanning and external subtitle discovery."""

import unittest
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import subtitles as subtitle_module


class TestGetVideo(unittest.TestCase):
    """Test the get_video function."""

    @patch("sickchill.oldbeard.subtitles.get_subtitles_path")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_external_subtitles_added_to_video_subtitles(self, mock_subliminal, mock_get_path):
        """External subtitles should be added to video.subtitles (not subtitle_languages)."""
        mock_get_path.return_value = "/fake/subs"

        mock_video = MagicMock()
        mock_video.subtitles = []
        mock_video.name = "video.mkv"
        mock_subliminal.scan_video.return_value = mock_video

        fake_external_sub = MagicMock(name="ExternalSubtitle")
        mock_subliminal.core.search_external_subtitles.return_value = {
            "video.en.srt": fake_external_sub,
        }

        result = subtitle_module.get_video("/fake/path/video.mkv")

        self.assertIs(result, mock_video)
        self.assertIn(fake_external_sub, result.subtitles)
        mock_subliminal.core.search_external_subtitles.assert_called_once_with(
            "/fake/path/video.mkv", directory="/fake/subs"
        )

    @patch("sickchill.oldbeard.subtitles.get_subtitles_path")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_external_subtitles_multiple(self, mock_subliminal, mock_get_path):
        """Multiple external subtitles should all be added."""
        mock_get_path.return_value = "/fake/subs"

        mock_video = MagicMock()
        mock_video.subtitles = []
        mock_video.name = "video.mkv"
        mock_subliminal.scan_video.return_value = mock_video

        sub_en = MagicMock(name="ExternalSubtitle-en")
        sub_fr = MagicMock(name="ExternalSubtitle-fr")
        mock_subliminal.core.search_external_subtitles.return_value = {
            "video.en.srt": sub_en,
            "video.fr.srt": sub_fr,
        }

        result = subtitle_module.get_video("/fake/path/video.mkv")

        self.assertEqual(len(result.subtitles), 2)
        self.assertIn(sub_en, result.subtitles)
        self.assertIn(sub_fr, result.subtitles)

    @patch("sickchill.oldbeard.subtitles.get_subtitles_path")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_no_external_subtitles_when_disabled(self, mock_subliminal, mock_get_path):
        """When subtitles=False, search_external_subtitles should not be called."""
        mock_get_path.return_value = "/fake/subs"

        mock_video = MagicMock()
        mock_video.subtitles = []
        mock_video.name = "video.mkv"
        mock_subliminal.scan_video.return_value = mock_video

        subtitle_module.get_video("/fake/path/video.mkv", subtitles=False)

        mock_subliminal.core.search_external_subtitles.assert_not_called()
