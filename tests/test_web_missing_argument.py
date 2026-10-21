"""Missing query args should not be logged as mako 500s."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, MissingArgumentError

from sickchill.views.home import Home
from sickchill.views.index import BaseHandler, WebHandler


def test_test_rename_missing_show_returns_generic_message():
    handler = Home.__new__(Home)
    handler.get_query_argument = MagicMock(return_value=None)
    handler._genericMessage = MagicMock(return_value="generic")

    assert handler.testRename() == "generic"
    handler._genericMessage.assert_called_once()
    assert handler._genericMessage.call_args.args[0] == "Error"
    assert "specify a show" in handler._genericMessage.call_args.args[1]


def test_async_call_reraises_missing_argument_error():
    inner = WebHandler.async_call.__wrapped__
    handler = WebHandler.__new__(WebHandler)

    def boom():
        raise MissingArgumentError("show")

    with pytest.raises(MissingArgumentError):
        inner(handler, boom, False)


class _NeedShowHandler(BaseHandler):
    def get(self):
        self.get_query_argument("show")
        self.write("ok")


class TestMissingArgumentHTTP(AsyncHTTPTestCase):
    def get_app(self):
        return Application([("/", _NeedShowHandler)])

    def test_missing_argument_returns_400_body(self):
        response = self.fetch("/")
        self.assertEqual(response.code, 400)
        self.assertTrue(response.body)
        body = response.body.decode("utf-8", errors="replace").lower()
        self.assertIn("400", body)
        self.assertNotIn("mako error", body)
