"""IMDb redirect/legacy title id resolution."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import helpers


class NormalizeImdbIdTests(unittest.TestCase):
    def test_normalizes_digits_and_prefixed(self):
        self.assertEqual(helpers.normalize_imdb_id("41154853"), "tt41154853")
        self.assertEqual(helpers.normalize_imdb_id("tt41154853"), "tt41154853")
        self.assertEqual(helpers.normalize_imdb_id("IMDB tt38840807"), "tt38840807")

    def test_empty_and_invalid(self):
        self.assertEqual(helpers.normalize_imdb_id(None), "")
        self.assertEqual(helpers.normalize_imdb_id(""), "")
        self.assertEqual(helpers.normalize_imdb_id("not-an-id"), "")


class ResolveImdbTitleIdTests(unittest.TestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(helpers.resolve_imdb_title_id(None), "")
        self.assertEqual(helpers.resolve_imdb_title_id(""), "")

    def test_follows_redirect_from_auxiliary_id(self):
        client = MagicMock()
        client.region = None
        client._get.return_value = {"id": "/title/tt38840807/"}

        self.assertEqual(helpers.resolve_imdb_title_id("tt41154853", client=client), "tt38840807")
        client._get.assert_called_once()
        params = client._get.call_args.kwargs["params"]
        self.assertEqual(params["tconst"], "tt41154853")

    def test_canonical_id_unchanged(self):
        client = MagicMock()
        client.region = None
        client._get.return_value = {"id": "/title/tt38840807/"}

        self.assertEqual(helpers.resolve_imdb_title_id("tt38840807", client=client), "tt38840807")

    def test_lookup_failure_returns_normalized(self):
        client = MagicMock()
        client.region = None
        client._get.side_effect = Exception("boom")

        self.assertEqual(helpers.resolve_imdb_title_id("41154853", client=client), "tt41154853")

    def test_non_dict_response_returns_normalized(self):
        client = MagicMock()
        client.region = None
        client._get.return_value = None

        self.assertEqual(helpers.resolve_imdb_title_id("tt41154853", client=client), "tt41154853")


class FetchImdbTitleRedirectTests(unittest.TestCase):
    @patch("sickchill.tv.ImdbFacade")
    @patch("sickchill.tv.helpers.resolve_imdb_title_id", return_value="tt38840807")
    @patch("sickchill.tv.Imdb")
    def test_fetch_uses_resolved_id(self, imdb_cls, resolve_id, facade_cls):
        from sickchill.tv import TVShow

        client = MagicMock()
        imdb_cls.return_value = client
        title = SimpleNamespace(imdb_id="tt41154853", title="Resolved Show")
        facade = MagicMock()
        facade.get_title.return_value = title
        facade_cls.return_value = facade

        show = object.__new__(TVShow)
        result = TVShow._fetch_imdb_title(show, "tt41154853")

        resolve_id.assert_called_once_with("tt41154853", client=client)
        facade_cls.assert_called_once_with(client=client)
        facade.get_title.assert_called_once_with("tt38840807")
        self.assertIs(result, title)
        self.assertEqual(result.imdb_id, "tt38840807")


if __name__ == "__main__":
    unittest.main()
