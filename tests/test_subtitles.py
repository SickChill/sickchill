"""Tests for subliminal 2.x compatibility in the subtitles module."""

import unittest
from unittest.mock import MagicMock, patch

import subliminal
import subliminal.score
import subliminal.subtitle
from babelfish import Language

from sickchill import settings
from sickchill.oldbeard import subtitles as subtitle_module


class TestGetVideo(unittest.TestCase):
    """Test the get_video function."""

    @patch("sickchill.oldbeard.subtitles.get_subtitles_path")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_external_subtitles_added_to_video_subtitles(self, mock_subliminal, mock_get_path):
        """External subtitles should be added to video.subtitles, not subtitle_languages."""
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


class TestScoreThresholds(unittest.TestCase):
    """Test that score thresholds use subliminal's actual scoring tables."""

    def test_perfect_match_score_uses_hash(self):
        """Perfect match score should be derived from the hash score, not hardcoded."""
        scores = subliminal.score.episode_scores
        perfect = scores["hash"] - scores.get("resolution", 0) - scores.get("video_codec", 0)
        non_perfect = scores.get("series", 0) + scores.get("year", 0) + scores.get("season", 0) + scores.get("episode", 0)
        # Must not be the old hardcoded value
        self.assertNotEqual(perfect, 213)
        # Must be positive and greater than non-perfect threshold
        self.assertGreater(perfect, 0)
        self.assertGreater(perfect, non_perfect)

    def test_non_perfect_match_score(self):
        """Non-perfect match score should sum series+year+season+episode."""
        scores = subliminal.score.episode_scores
        expected = scores.get("series", 0) + scores.get("year", 0) + scores.get("season", 0) + scores.get("episode", 0)
        # Must not be the old hardcoded value
        self.assertNotEqual(expected, 198)
        # Must be positive
        self.assertGreater(expected, 0)


class TestGetSubtitlePath(unittest.TestCase):
    """Test that get_subtitle_path receives correct string arguments."""

    def test_single_subtitle_path(self):
        """Single subtitle mode should pass empty string suffix."""
        result = subliminal.subtitle.get_subtitle_path("/path/to/video.mkv", "")
        self.assertEqual(result, "/path/to/video.srt")

    def test_multi_subtitle_path_with_language(self):
        """Multi subtitle mode should pass language code as string suffix."""
        lang = Language("eng")
        result = subliminal.subtitle.get_subtitle_path("/path/to/video.mkv", f".{lang.alpha2}")
        self.assertEqual(result, "/path/to/video.en.srt")

    def test_none_suffix_crashes(self):
        """Passing None as suffix should raise TypeError (the old bug)."""
        with self.assertRaises(TypeError):
            subliminal.subtitle.get_subtitle_path("/path/to/video.mkv", None)

    def test_language_object_suffix_crashes(self):
        """Passing a Language object as suffix should raise TypeError (the old bug)."""
        lang = Language("eng")
        with self.assertRaises(TypeError):
            subliminal.subtitle.get_subtitle_path("/path/to/video.mkv", lang)


class TestRefineVideo(unittest.TestCase):
    """Test refine_video for subliminal 2.x compatibility."""

    def test_episode_attribute_is_readonly_property(self):
        """video.episode should be a read-only property in subliminal 2.x."""
        ep = subliminal.Episode("test.mkv", series="Test", season=1, episodes=[5])
        self.assertEqual(ep.episode, 5)
        with self.assertRaises(AttributeError):
            ep.episode = 10  # noqa: B009

    def test_episodes_attribute_is_settable(self):
        """video.episodes should be settable."""
        ep = subliminal.Episode("test.mkv", series="Test", season=1, episodes=[5])
        ep.episodes = [10]
        self.assertEqual(ep.episode, 10)

    @patch("sickchill.oldbeard.subtitles.guessit")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_refine_video_sets_episodes_not_episode(self, mock_subliminal, mock_guessit):
        """refine_video should set video.episodes (list) not video.episode (property)."""
        mock_video = MagicMock(spec=[])  # no spec so setattr works freely
        mock_video.episodes = None
        mock_video.release_group = "TestGroup"
        mock_video.season = 1
        mock_video.series = "TestShow"
        mock_video.series_imdb_id = None
        mock_video.size = None
        mock_video.title = None
        mock_video.year = None
        mock_video.series_tvdb_id = None
        mock_video.tvdb_id = None
        mock_video.source = None
        mock_video.resolution = None

        mock_episode = MagicMock()
        mock_episode.release_name = None
        mock_episode.episode = 5
        mock_episode.show.subtitles_sc_metadata = False

        subtitle_module.refine_video(mock_video, mock_episode)

        # Should have set episodes to [5], not tried to set episode
        self.assertEqual(mock_video.episodes, [5])

    @patch("sickchill.oldbeard.subtitles.guessit")
    @patch("sickchill.oldbeard.subtitles.subliminal")
    def test_refine_video_handles_guessing_error(self, mock_subliminal, mock_guessit):
        """refine_video should handle GuessingError from Episode.fromguess gracefully."""
        mock_video = MagicMock()
        mock_video.episodes = [5]

        mock_episode = MagicMock()
        mock_episode.release_name = "Some.Bad.Release.Name"
        mock_episode.episode = 5
        mock_episode.show.subtitles_sc_metadata = False

        mock_guessit.return_value = {"type": "episode"}  # Missing 'title' and 'episode'
        mock_subliminal.Episode.fromguess.side_effect = ValueError("Insufficient data")

        # Should not raise
        subtitle_module.refine_video(mock_video, mock_episode)


class TestComputeScore(unittest.TestCase):
    """Test that compute_score is called correctly."""

    def test_compute_score_signature(self):
        """compute_score should accept subtitle and video without hearing_impaired."""
        import inspect

        sig = inspect.signature(subliminal.score.compute_score)
        params = list(sig.parameters.keys())
        self.assertEqual(params[0], "subtitle")
        self.assertEqual(params[1], "video")
        # hearing_impaired should NOT be a named parameter (only **kwargs)
        self.assertNotIn("hearing_impaired", params)
