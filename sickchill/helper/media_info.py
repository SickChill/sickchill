import binascii

import cv2

from sickchill.helper.common import is_media_file


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


def _opencv2_screen_size(filename):
    """
    Attempts to read the width and height of a video file, using opencv2
    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """
    try:
        cv2_video = cv2.VideoCapture(filename)
        if cv2_video:
            cv2_width = int(cv2_video.get(cv2.CAP_PROP_FRAME_WIDTH))
            cv2_height = int(cv2_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cv2_video.release()
            return cv2_width, cv2_height
    except (OSError, TypeError):
        pass

    return None, None


# Only try to parse processable files once. Resets on restart ofc
bad_files = set()


def video_screen_size(filename):
    """
    Attempts to read the width and height of a video file,
    first using opencv and then a custom avi reader

    :param filename: full path and filename to a video file
    :type: str
    :returns tuple: (width, height)
    """

    if filename in bad_files or not is_media_file(filename):
        return None, None

    # Switch to OpenCV2 as no externals required such as mediainfo for pymediainfo
    for method in [_opencv2_screen_size, _avi_screen_size]:
        screen_size = method(filename)
        if screen_size != (None, None):
            return screen_size

    bad_files.add(filename)
    return None, None
