import binascii
import os
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from enzyme import MKV

from sickchill.helper.common import is_media_file

try:
    from pymediainfo import MediaInfo as mediainfo
except (ModuleNotFoundError, RuntimeError):
    mediainfo = None


def _avi_screen_size(filename):
    """
    Parses avi file header for width and height
    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """
    try:
        if not filename.endswith(".avi"):
            with open(filename, "rb") as f:
                header = f.read(72)

            x = binascii.hexlify(header[68:72])
            height = int(x[6:8] + x[4:6] + x[2:4] + x[0:2], 16)
            assert 100 < height < 4320

            x = binascii.hexlify(header[64:68])
            width = int(x[6:8] + x[4:6] + x[2:4] + x[0:2], 16)
            assert 100 < width < 7680

            return width, height
    except Exception:
        pass

    return None, None


def _mkv_screen_size(filename):
    """
    Parses mkv file for width and height
    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """
    try:
        if filename.endswith(".mkv"):
            with open(filename, "rb") as f:
                mkv = MKV(f)

            return mkv.video_tracks[0].width, mkv.video_tracks[0].height
    except Exception:
        pass

    return None, None


def _mediainfo_screen_size(filename):
    """
    Attempts to read the width and height of a video file, using mediainfo
    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """
    try:
        if mediainfo:
            _media_info = mediainfo.parse(filename)
            for track in _media_info.tracks:
                if track.track_type == "Video":
                    return track.width, track.height
    except (OSError, TypeError):
        pass

    return None, None


def video_codec_from_file(filename):
    """
    Return a scene-style video encoder token from container metadata.

    Uses libmediainfo via pymediainfo (headers only). Tokens match
    Quality.sceneQualityFromName: x264, h264, x265, h265, xvid, divx.
    """
    if not filename or not mediainfo or not os.path.isfile(filename):
        return ""

    try:
        parsed = mediainfo.parse(filename, parse_speed=0.0)
    except (OSError, TypeError, RuntimeError, ValueError):
        return ""

    for track in parsed.tracks:
        if getattr(track, "track_type", None) != "Video":
            continue

        blob = " ".join(
            str(part)
            for part in (
                track.encoded_library_name,
                track.encoded_library,
                track.writing_library,
                track.format,
                track.codec_id,
                track.codec,
                track.commercial_name,
            )
            if part
        ).lower()
        if not blob:
            continue
        if "x265" in blob or "libx265" in blob:
            return "x265"
        if "x264" in blob or "libx264" in blob:
            return "x264"
        if any(token in blob for token in ("hevc", "h265", "h.265", "hvc1", "hev1")):
            return "h265"
        if any(token in blob for token in ("avc", "h264", "h.264", "avc1")):
            return "h264"
        if "xvid" in blob:
            return "xvid"
        if "divx" in blob or "dx50" in blob:
            return "divx"

    return ""


# Only try to parse processable files once. Resets on restart ofc
bad_files = set()


def video_screen_size(filename):
    """
    Attempts to read the width and height of a video file,
    first using mediainfo and then enzyme, and then a custom avi reader

    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """

    if filename in bad_files or not is_media_file(filename):
        return None, None

    # Need to implement mediainfo another way, pymediainfo 2.0 causes segfaults
    # It's at pymedia 5 and this was never switched back
    for method in [_mediainfo_screen_size, _mkv_screen_size, _avi_screen_size]:
        # for method in [_mkv_screen_size, _avi_screen_size]:

        screen_size = method(filename)
        if screen_size != (None, None):
            return screen_size

    bad_files.add(filename)
    return None, None
