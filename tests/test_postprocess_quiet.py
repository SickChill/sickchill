"""Regression: nzbToMedia quiet=1 must get plain text, not the HTML post-process page."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class ProcessEpisodeQuietTests(unittest.TestCase):
    def _handler(self, query: dict | None = None, form: dict | None = None, args: dict | None = None):
        """Build a PostProcess stub.

        Prefer separate ``query`` (dir/type) and ``form`` (proc_dir/proc_type) maps so
        script vs UI parameter groups are exercised independently. ``args`` remains
        as a combined fallback for older-style cases.
        """
        from sickchill.views.manage.post_processing import PostProcess

        query = dict(query or {})
        form = dict(form or {})
        if args:
            # Combined bag: treat as either source for get_argument lookups.
            query = {**args, **query}
            form = {**args, **form}

        def get_argument(name, default=None):
            if name in query:
                return query[name]
            if name in form:
                return form[name]
            return default

        handler = PostProcess.__new__(PostProcess)
        handler.get_argument = get_argument
        handler.redirect = MagicMock(return_value="REDIRECT")
        handler.set_header = MagicMock()
        handler._genericMessage = MagicMock(return_value="HTML")
        return handler

    @patch("sickchill.views.manage.post_processing.settings")
    def test_quiet_returns_plain_text(self, mock_settings):
        mock_settings.postProcessorTaskScheduler.action.add_item.return_value = "Processing in folder /downloads/show\nSuccessfully processed\n"
        handler = self._handler(
            form={
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
        handler = self._handler(form={"proc_dir": "/downloads/show"})
        result = handler.processEpisode()
        self.assertEqual(result, "HTML")
        handler._genericMessage.assert_called_once()

    def test_missing_dir_redirects(self):
        handler = self._handler()
        self.assertEqual(handler.processEpisode(), "REDIRECT")
        handler.redirect.assert_called_once_with("/home/postprocess/")

    @patch("sickchill.views.manage.post_processing.settings")
    def test_script_query_dir_and_type(self, mock_settings):
        """nzbToMedia-style GET: dir + type query params."""
        add_item = mock_settings.postProcessorTaskScheduler.action.add_item
        add_item.return_value = "ok\n"
        handler = self._handler(query={"dir": "/downloads/script", "type": "auto", "quiet": "1", "nzbName": "ep.nzb"})
        result = handler.processEpisode()
        self.assertEqual(result, "ok\n")
        add_item.assert_called_once()
        args, kwargs = add_item.call_args
        self.assertEqual(args[0], "/downloads/script")
        self.assertEqual(args[1], "ep.nzb")
        self.assertEqual(kwargs["mode"], "auto")

    @patch("sickchill.views.manage.post_processing.settings")
    def test_ui_form_proc_dir_and_proc_type(self, mock_settings):
        """Browser form POST: proc_dir + proc_type body params."""
        add_item = mock_settings.postProcessorTaskScheduler.action.add_item
        add_item.return_value = "ok\n"
        handler = self._handler(form={"proc_dir": "/downloads/ui", "proc_type": "manual"})
        handler.processEpisode()
        add_item.assert_called_once()
        args, kwargs = add_item.call_args
        self.assertEqual(args[0], "/downloads/ui")
        self.assertEqual(kwargs["mode"], "manual")

    @patch("sickchill.views.manage.post_processing.settings")
    def test_empty_type_falls_back_to_proc_type(self, mock_settings):
        """Empty type must not hide a set proc_type."""
        add_item = mock_settings.postProcessorTaskScheduler.action.add_item
        add_item.return_value = "ok\n"
        handler = self._handler(query={"dir": "/downloads/mixed", "type": ""}, form={"proc_type": "auto"})
        handler.processEpisode()
        self.assertEqual(add_item.call_args.kwargs["mode"], "auto")

    @patch("sickchill.views.manage.post_processing.settings")
    def test_dir_preferred_over_proc_dir(self, mock_settings):
        add_item = mock_settings.postProcessorTaskScheduler.action.add_item
        add_item.return_value = "ok\n"
        handler = self._handler(query={"dir": "/from-query"}, form={"proc_dir": "/from-form"})
        handler.processEpisode()
        self.assertEqual(add_item.call_args.args[0], "/from-query")

    @patch("sickchill.views.manage.post_processing.settings")
    def test_default_mode_is_manual(self, mock_settings):
        add_item = mock_settings.postProcessorTaskScheduler.action.add_item
        add_item.return_value = "ok\n"
        handler = self._handler(form={"proc_dir": "/downloads/default"})
        handler.processEpisode()
        self.assertEqual(add_item.call_args.kwargs["mode"], "manual")


if __name__ == "__main__":
    unittest.main()
