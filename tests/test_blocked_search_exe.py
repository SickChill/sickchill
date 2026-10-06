"""Skip .exe provider hits at search/cache/snatch."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from sickchill.oldbeard.search import snatch_episode
from sickchill.oldbeard.tvcache import RSSTorrentMixin, TVCache
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.result_classes import SearchResult


class BlockedSearchExeTests(unittest.TestCase):
    def test_add_cache_entry_skips_exe_title(self):
        cache = TVCache(GenericProvider("Test"))
        with patch("sickchill.oldbeard.tvcache.NameParser") as parser:
            result = cache.add_cache_entry("Show.Name.S01E01.720p.HDTV.x264.exe", "https://example.com/dl/file.torrent", 1, 1, 0)
        self.assertIsNone(result)
        parser.assert_not_called()

    def test_add_cache_entry_skips_exe_url(self):
        cache = TVCache(GenericProvider("Test"))
        with patch("sickchill.oldbeard.tvcache.NameParser") as parser:
            result = cache.add_cache_entry("Show.Name.S01E01.720p.HDTV.x264-GROUP", "https://example.com/dl/Show.S01E01.exe", 1, 1, 0)
        self.assertIsNone(result)
        parser.assert_not_called()

    def test_parse_feed_item_skips_exe_title(self):
        from sickchill.oldbeard.bs4_parser import BS4Parser

        xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Show.Name.S01E01.720p.HDTV.x264.exe</title>
      <link>https://example.com/dl/file.torrent</link>
      <enclosure url="https://example.com/dl/file.torrent" length="123" type="application/x-bittorrent"/>
    </item>
  </channel>
</rss>
"""
        with BS4Parser(xml, language="xml") as feed:
            result = RSSTorrentMixin.parse_feed_item(feed.find("item"), "https://example.com")
        self.assertIsNone(result)

    def test_snatch_episode_refuses_exe(self):
        result = SearchResult([])
        result.name = "Show.Name.S01E01.720p.HDTV.x264.exe"
        result.url = "https://example.com/dl/file.torrent"
        self.assertFalse(snatch_episode(result))
