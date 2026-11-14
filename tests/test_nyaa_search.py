"""Nyaa daily/backlog RSS params and provider-option defaults."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from configobj import ConfigObj

from sickchill.oldbeard.providers.nyaa import Provider
from sickchill.plugins.providers.config import _apply_provider_options


class TestNyaaSearch(unittest.TestCase):
    def _provider(self, confirmed=False, minseed=0):
        provider = Provider()
        provider.confirmed = confirmed
        provider.minseed = minseed
        provider.minleech = 0
        provider.show = SimpleNamespace(is_anime=True)
        return provider

    def test_backlog_uses_no_filter_when_not_confirmed(self):
        provider = self._provider(confirmed=False)
        captured = {}

        def fake_get_url(url, params=None, **_kwargs):
            captured["url"] = url
            captured["params"] = params
            return ""

        provider.get_url = fake_get_url
        provider.search({"Episode": {"KILL BLUE S01E01"}})

        self.assertEqual(captured["params"]["page"], "rss")
        self.assertEqual(captured["params"]["c"], "1_0")
        self.assertEqual(captured["params"]["f"], "0")
        self.assertEqual(captured["params"]["q"], "KILL BLUE S01E01")

    def test_backlog_trusted_only_when_confirmed(self):
        provider = self._provider(confirmed=True)
        captured = {}

        def fake_get_url(url, params=None, **_kwargs):
            captured["params"] = params
            return ""

        provider.get_url = fake_get_url
        provider.search({"Episode": {"KILL BLUE S01E01"}})
        self.assertEqual(captured["params"]["f"], "2")

    def test_daily_rss_omits_query(self):
        provider = self._provider(confirmed=False)
        captured = {}

        def fake_get_url(url, params=None, **_kwargs):
            captured["params"] = params
            return ""

        provider.get_url = fake_get_url
        provider.search({"RSS": {""}})
        self.assertEqual(captured["params"]["f"], "0")
        self.assertNotIn("q", captured["params"])

    def test_skips_non_anime_show(self):
        provider = self._provider()
        provider.show = SimpleNamespace(is_anime=False)
        provider.get_url = lambda *args, **kwargs: self.fail("should not request")
        self.assertEqual(provider.search({"Episode": {"KILL BLUE S01E01"}}), [])

    def test_empty_cfg_keeps_nyaa_init_defaults(self):
        provider = Provider()
        self.assertFalse(provider.confirmed)
        self.assertEqual(provider.minseed, 0)
        _apply_provider_options(ConfigObj(), provider)
        self.assertFalse(provider.confirmed)
        self.assertEqual(provider.minseed, 0)

    @patch("sickchill.oldbeard.providers.nyaa.BS4Parser")
    def test_multiple_modes_keep_earlier_results(self, parser_cls):
        provider = self._provider(confirmed=False, minseed=0)

        class _Item:
            pass

        class _Feed:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def find_all(self, _tag):
                return [_Item()]

        parser_cls.return_value = _Feed()
        titles = iter(["first", "second"])

        def fake_parse(_item, _url, size_units=None):
            return {"title": next(titles), "link": "http://x", "size": 1, "seeders": 1, "leechers": 0, "hash": "h"}

        provider.parse_feed_item = fake_parse
        provider.get_url = lambda *args, **kwargs: "<rss/>"

        results = provider.search({"Episode": {"A"}, "Season": {"B"}})
        names = {item["title"] for item in results}
        self.assertEqual(names, {"first", "second"})


class TestNyaaFeedSize(unittest.TestCase):
    def test_parse_feed_item_reads_nyaa_size_gib(self):
        from sickchill.oldbeard.bs4_parser import BS4Parser
        from sickchill.oldbeard.tvcache import RSSTorrentMixin

        xml = """<?xml version="1.0"?>
<rss xmlns:nyaa="https://nyaa.si/xmlns/nyaa" version="2.0">
  <channel>
    <item>
      <title>KILL BLUE S01E01</title>
      <link>https://nyaa.si/download/2113348.torrent</link>
      <guid isPermaLink="true">https://nyaa.si/view/2113348</guid>
      <nyaa:seeders>8</nyaa:seeders>
      <nyaa:leechers>12</nyaa:leechers>
      <nyaa:infoHash>eb364f3353a0f4057ce6bb8899b1eb0a59fc3c05</nyaa:infoHash>
      <nyaa:size>1.4 GiB</nyaa:size>
    </item>
  </channel>
</rss>
"""
        with BS4Parser(xml, language="xml") as feed:
            result = RSSTorrentMixin.parse_feed_item(
                feed.find("item"),
                "https://nyaa.si",
                size_units=Provider().size_units,
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["size"], int(1.4 * 1024**3))
        self.assertGreater(result["size"], 0)
        self.assertEqual(result["seeders"], 8)
        self.assertEqual(result["leechers"], 12)
        self.assertEqual(result["hash"], "eb364f3353a0f4057ce6bb8899b1eb0a59fc3c05")
