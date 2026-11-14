"""Scene-quality encoder from filename vs libmediainfo file metadata."""

from types import SimpleNamespace
from unittest.mock import patch

from sickchill.helper.media_info import video_codec_from_file
from sickchill.oldbeard.common import Quality


def test_scene_quality_from_name_x264():
    assert Quality.sceneQualityFromName("Show.S01E01.720p.HDTV.x264-GROUP", Quality.HDTV) == " x264"


def test_scene_quality_from_name_file_codec_overrides_release_name():
    encoder = Quality.sceneQualityFromName("Show.S01E01.720p.HDTV.x264-GROUP", Quality.HDTV, file_codec="x265")
    assert encoder == " x265"


def test_scene_quality_from_name_none_release_name():
    assert Quality.sceneQualityFromName(None, Quality.HDTV) == ""
    assert Quality.sceneQualityFromName(None, Quality.HDTV, file_codec="h264") == " h264"


def test_scene_quality_from_name_sddvd_rip_type_with_file_codec():
    encoder = Quality.sceneQualityFromName("Show.S01E01.DVDRip-GROUP", Quality.SDDVD, file_codec="x264")
    assert encoder == " DVDRip x264"


def test_scene_quality_from_file_falls_back_to_name(tmp_path):
    missing = tmp_path / "missing.mkv"
    encoder = Quality.sceneQualityFromFile(str(missing), Quality.HDTV, "Show.S01E01.720p.HDTV.x264-GROUP")
    assert encoder == " x264"


def _video_track(**fields):
    defaults = {
        "track_type": "Video",
        "encoded_library_name": None,
        "encoded_library": None,
        "writing_library": None,
        "format": None,
        "codec_id": None,
        "codec": None,
        "commercial_name": None,
    }
    defaults.update(fields)
    return SimpleNamespace(**defaults)


def test_video_codec_from_file_prefers_x264_library(tmp_path):
    media = tmp_path / "episode.mkv"
    media.write_bytes(b"not a real mkv")
    parsed = SimpleNamespace(tracks=[_video_track(encoded_library_name="x264 - core 164", format="AVC")])
    with patch("sickchill.helper.media_info.mediainfo") as mock_info:
        mock_info.parse.return_value = parsed
        assert video_codec_from_file(str(media)) == "x264"


def test_video_codec_from_file_hevc_without_x265(tmp_path):
    media = tmp_path / "episode.mp4"
    media.write_bytes(b"not a real mp4")
    parsed = SimpleNamespace(tracks=[_video_track(format="HEVC", codec_id="hvc1")])
    with patch("sickchill.helper.media_info.mediainfo") as mock_info:
        mock_info.parse.return_value = parsed
        assert video_codec_from_file(str(media)) == "h265"


def test_video_codec_from_file_missing_path():
    assert video_codec_from_file("") == ""
    assert video_codec_from_file("/no/such/file.mkv") == ""
