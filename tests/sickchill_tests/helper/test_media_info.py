"""AVI header width and height parsing."""

import tempfile
import unittest
from pathlib import Path

from sickchill.helper.media_info import _avi_screen_size


def _avi_header(width: int, height: int) -> bytes:
    header = bytearray(72)
    header[64:68] = width.to_bytes(4, "little")
    header[68:72] = height.to_bytes(4, "little")
    return bytes(header)


class AviScreenSizeTests(unittest.TestCase):
    def _write(self, directory: str, name: str, width: int, height: int) -> str:
        path = Path(directory) / name
        path.write_bytes(_avi_header(width, height))
        return str(path)

    def test_normal_avi_within_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "sample.avi", 640, 480)
            self.assertEqual(_avi_screen_size(path), (640, 480))

    def test_avi_outside_bounds_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "wide.avi", 8000, 480)
            self.assertEqual(_avi_screen_size(path), (None, None))

    def test_non_avi_is_not_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, "sample.mkv", 640, 480)
            self.assertEqual(_avi_screen_size(path), (None, None))
