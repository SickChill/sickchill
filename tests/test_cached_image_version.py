"""Replaced cache artwork must get a new ?v= hash on the next page."""

import os
import tempfile
import unittest

from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.views.server_settings import SickChillStaticFileHandler


class CachedImageVersionTests(unittest.TestCase):
    def tearDown(self):
        SickChillStaticFileHandler.reset()

    def test_rewritten_file_gets_a_new_version_after_the_hash_is_dropped(self):
        with tempfile.TemporaryDirectory() as root:
            relative = os.path.join("cache", "images", "thumbnails", "469744.poster.jpg")
            path = os.path.join(root, relative)
            os.makedirs(os.path.dirname(path))
            with open(path, "wb") as handle:
                handle.write(b"first-poster")

            settings = {"static_path": root}
            SickChillStaticFileHandler.reset()
            first = SickChillStaticFileHandler.get_version(settings, relative.replace(os.sep, "/"))
            with open(path, "wb") as handle:
                handle.write(b"replaced-poster")
            # Tornado keeps the first hash until it is dropped.
            self.assertEqual(SickChillStaticFileHandler.get_version(settings, relative.replace(os.sep, "/")), first)

            SickChillStaticFileHandler.drop_cached_version(path)
            fresh = SickChillStaticFileHandler.get_version(settings, relative.replace(os.sep, "/"))
            self.assertNotEqual(fresh, first)
            self.assertTrue(fresh)

    def test_write_image_drops_the_cached_version(self):
        with tempfile.TemporaryDirectory() as root:
            relative = "cache/images/1.poster.jpg"
            path = os.path.join(root, "cache", "images", "1.poster.jpg")
            os.makedirs(os.path.dirname(path))
            with open(path, "wb") as handle:
                handle.write(b"old")
            settings = {"static_path": root}
            SickChillStaticFileHandler.reset()
            old = SickChillStaticFileHandler.get_version(settings, relative)

            self.assertTrue(GenericMetadata._write_image(b"new-art", path, overwrite=True))
            self.assertNotEqual(SickChillStaticFileHandler.get_version(settings, relative), old)
