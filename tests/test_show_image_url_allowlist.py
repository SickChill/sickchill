"""SSRF guards for show artwork URL fetching."""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock, patch

from sickchill.providers.metadata.helpers import getShowImage, is_allowed_show_image_url


def _ok_response(content: bytes = b"IMG"):
    response = MagicMock()
    response.is_redirect = False
    response.status_code = 200
    response.content = content
    response.raise_for_status = MagicMock()
    response.close = MagicMock()
    response.iter_content = MagicMock(return_value=iter([content]))
    response.url = "https://artworks.thetvdb.com/banners/x.jpg"
    return response


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
        response = _ok_response(b"IMG")
        get_url.return_value = response

        self.assertEqual(getShowImage("https://artworks.thetvdb.com/banners/x.jpg", timeout=10), b"IMG")
        get_url.assert_called_once()
        kwargs = get_url.call_args.kwargs
        self.assertFalse(kwargs.get("allow_redirects"))
        self.assertTrue(kwargs.get("stream"))
        self.assertAlmostEqual(kwargs.get("timeout"), 10, delta=0.05)
        response.close.assert_called()

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_revalidates_redirect_target(self, get_url):
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.status_code = 302
        redirect.headers = {"Location": "https://127.0.0.1/internal"}
        redirect.url = "https://artworks.thetvdb.com/banners/x.jpg"
        redirect.raise_for_status = MagicMock()
        redirect.close = MagicMock()
        get_url.return_value = redirect

        self.assertIsNone(getShowImage("https://artworks.thetvdb.com/banners/x.jpg"))
        get_url.assert_called_once()
        redirect.close.assert_called()

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_follows_allowlisted_redirect(self, get_url):
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.status_code = 302
        redirect.headers = {"Location": "https://artworks.thetvdb.com/banners/y.jpg"}
        redirect.url = "https://artworks.thetvdb.com/banners/x.jpg"
        redirect.raise_for_status = MagicMock()
        redirect.close = MagicMock()

        final = _ok_response(b"OK")
        final.url = "https://artworks.thetvdb.com/banners/y.jpg"

        get_url.side_effect = [redirect, final]
        self.assertEqual(getShowImage("https://artworks.thetvdb.com/banners/x.jpg"), b"OK")
        self.assertEqual(get_url.call_count, 2)
        # Second hop should receive a remaining timeout budget, not a fresh full timeout reset only
        self.assertIn("timeout", get_url.call_args_list[0].kwargs)
        self.assertIn("timeout", get_url.call_args_list[1].kwargs)
        self.assertTrue(get_url.call_args_list[0].kwargs.get("stream"))
        self.assertTrue(get_url.call_args_list[1].kwargs.get("stream"))
        redirect.close.assert_called()
        final.close.assert_called()

    @patch("sickchill.providers.metadata.helpers.helpers.getURL")
    def test_slow_chunks_cannot_exceed_deadline(self, get_url):
        """Frequent slow chunks must abort once the shared deadline is exhausted."""

        def slow_chunks(_chunk_size=0):
            # Many small delays would exceed a short deadline if the body were read unbounded.
            for _ in range(50):
                time.sleep(0.05)
                yield b"x" * 1024

        response = MagicMock()
        response.is_redirect = False
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.close = MagicMock()
        response.iter_content = MagicMock(side_effect=slow_chunks)
        response.url = "https://artworks.thetvdb.com/banners/slow.jpg"
        get_url.return_value = response

        started = time.monotonic()
        self.assertIsNone(getShowImage("https://artworks.thetvdb.com/banners/slow.jpg", timeout=0.2))
        elapsed = time.monotonic() - started
        # Should stop near the deadline, not after all 50*0.05s chunks (~2.5s)
        self.assertLess(elapsed, 1.0)
        response.close.assert_called()
        self.assertTrue(get_url.call_args.kwargs.get("stream"))


class GetURLRedirectHandlingTests(unittest.TestCase):
    def test_disabled_redirects_do_not_return_redirect_body_as_text(self):
        """Jackett-style callers use returns=text with allow_redirects=False — must not parse 3xx bodies."""
        from sickchill.oldbeard import helpers as oldbeard_helpers

        session = MagicMock()
        redirect = MagicMock()
        redirect.is_redirect = True
        redirect.status_code = 302
        redirect.headers = {"Location": "https://example.invalid/next"}
        redirect.text = "<html>redirect</html>"
        redirect.raise_for_status = MagicMock()
        session.request.return_value = redirect

        result = oldbeard_helpers.getURL(
            "http://127.0.0.1:9117/api",
            session=session,
            returns="text",
            allow_redirects=False,
            allow_proxy=False,
        )
        self.assertEqual(result, "")
        redirect.raise_for_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
