"""Regression: nzbToMedia quiet=1 must get plain text, not the HTML post-process page."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class ProcessEpisodeQuietTests(unittest.TestCase):
    def _handler(self, args: dict):
        from sickchill.views.manage.post_processing import PostProcess

        handler = PostProcess.__new__(PostProcess)
        handler.get_argument = lambda name, default=None: args.get(name, default)
        handler.redirect = MagicMock(return_value="REDIRECT")
        handler.set_header = MagicMock()
        handler._genericMessage = MagicMock(return_value="HTML")
        return handler

    @patch("sickchill.views.manage.post_processing.settings")
    def test_quiet_returns_plain_text(self, mock_settings):
        mock_settings.postProcessorTaskScheduler.action.add_item.return_value = "Processing in folder /downloads/show\nSuccessfully processed\n"
        handler = self._handler(
            {
                "proc_dir": "/downloads/show",
                "nzbName": "show.nzb",
                "quiet": "1",
                "failed": "0",
            }
        )
        result = handler.processEpisode()
        self.assertIn("Successfully processed", result)
        self.assertNotEqual(result, "HTML")
        handler.set_header.assert_called_with("Content-Type", "text/plain; charset=utf-8")
        handler._genericMessage.assert_not_called()

    @patch("sickchill.views.manage.post_processing.settings")
    def test_without_quiet_uses_html_message(self, mock_settings):
        mock_settings.postProcessorTaskScheduler.action.add_item.return_value = "Successfully processed\n"
        handler = self._handler({"proc_dir": "/downloads/show"})
        result = handler.processEpisode()
        self.assertEqual(result, "HTML")
        handler._genericMessage.assert_called_once()

    def test_missing_dir_redirects(self):
        handler = self._handler({})
        self.assertEqual(handler.processEpisode(), "REDIRECT")
        handler.redirect.assert_called_once_with("/home/postprocess/")


if __name__ == "__main__":
    unittest.main()
