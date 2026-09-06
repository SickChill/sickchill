"""SSRF guards for show artwork URL fetching."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from sickchill.providers.metadata.helpers import getShowImage, is_allowed_show_image_url


class AllowlistTests(unittest.TestCase):
    def test_allows_known_hosts(self):
        self.assertTrue(is_allowed_show_image_url("https://artworks.thetvdb.com/banners/graphical/1.jpg"))
        self.assertTrue(is_allowed_show_image_url("https://assets.fanart.tv/fanart/tv/1/tvposter.jpg"))
        self.assertTrue(is_allowed_show_image_url("http://image.tmdb.org/t/p/original/x.jpg"))

    def test_blocks_other_hosts_and_schemes(self):
        self.assertFalse(is_allowed_show_image_url("https://evil.example/pwn.jpg"))
        self.assertFalse(is_allowed_show_image_url("https://127.0.0.1/secret"))
        self.assertFalse(is_allowed_show_image_url("https://artworks.thetvdb.com.evil.example/x.jpg"))
        self.assertFalse(is_allowed_show_image_url("file:///etc/passwd"))
        self.assertFalse(is_allowed_show_image_url("https://user:pass@artworks.thetvdb.com/banners/x.jpg"))
        self.assertFalse(is_allowed_show_image_url(""))
        self.assertFalse(is_allowed_show_image_url(None))


class GetShowImageSSRFTests(unittest.TestCase):
    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_blocks_before_fetch(self, get_url):
        self.assertIsNone(getShowImage("https://127.0.0.1/admin"))
        get_url.assert_not_called()

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_fetches_allowlisted(self, get_url):
        response = MagicMock()
        response.is_redirect = False
        response.status_code = 200
        response.content = b"IMG"
        response.raise_for_status = MagicMock()
        get_url.return_value = response

        self.assertEqual(getShowImage("https://artworks.thetvdb.com/banners/x.jpg"), b"IMG")
        get_url.assert_called_once()
        kwargs = get_url.call_args.kwargs
        self.assertFalse(kwargs.get("allow_redirects"))

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_revalidates_redirect_target(self, get_url):
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.status_code = 302
        redirect.headers = {"Location": "https://127.0.0.1/internal"}
        redirect.url = "https://artworks.thetvdb.com/banners/x.jpg"
        redirect.raise_for_status = MagicMock()
        get_url.return_value = redirect

        self.assertIsNone(getShowImage("https://artworks.thetvdb.com/banners/x.jpg"))
        get_url.assert_called_once()

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_follows_allowlisted_redirect(self, get_url):
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.status_code = 302
        redirect.headers = {"Location": "https://artworks.thetvdb.com/banners/y.jpg"}
        redirect.url = "https://artworks.thetvdb.com/banners/x.jpg"
        redirect.raise_for_status = MagicMock()

        final = MagicMock()
        final.is_redirect = False
        final.status_code = 200
        final.content = b"OK"
        final.raise_for_status = MagicMock()

        get_url.side_effect = [redirect, final]
        self.assertEqual(getShowImage("https://artworks.thetvdb.com/banners/x.jpg"), b"OK")
        self.assertEqual(get_url.call_count, 2)


if __name__ == "__main__":
    unittest.main()
