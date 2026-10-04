"""TorrentDay Provider Options category checkboxes."""

from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.oldbeard.providers.torrentday import DEFAULT_TV_CATEGORIES, Provider
from sickchill.plugins.providers.config import _apply_provider_options, _provider_to_section
from sickchill.plugins.settings import write_provider_section


class TestTorrentDayTvCategories(unittest.TestCase):
    def test_default_rebuild_matches_legacy_map(self):
        provider = Provider()
        self.assertFalse(provider.uses_configurable_categories)
        self.assertEqual(provider.tv_categories, DEFAULT_TV_CATEGORIES)
        self.assertEqual(provider.categories["Episode"], {"2": 1, "26": 1, "7": 1, "24": 1, "34": 1, "29": 1})
        self.assertEqual(provider.categories["Season"], {"14": 1})
        self.assertEqual(provider.categories["RSS"], {"2": 1, "26": 1, "7": 1, "24": 1, "34": 1, "29": 1, "14": 1})
        labels = dict(provider.tv_category_choices)
        self.assertEqual(labels["29"], "Anime")
        self.assertEqual(labels["30"], "Documentary")
        self.assertNotIn("14", labels)
        self.assertIn("104", labels)
        self.assertIn("32", labels)

    def test_unchecking_480p_drops_episode_and_rss(self):
        provider = Provider()
        provider.set_tv_categories("2,26,7,34,29")
        self.assertNotIn("24", provider.categories["Episode"])
        self.assertNotIn("24", provider.categories["RSS"])
        self.assertEqual(provider.categories["Season"], {"14": 1})
        self.assertEqual(provider.categories["RSS"]["14"], 1)

    def test_packs_always_on_season_and_rss(self):
        provider = Provider()
        provider.set_tv_categories("2,26,7,24,34,29")
        self.assertEqual(provider.categories["Season"], {"14": 1})
        self.assertEqual(provider.categories["RSS"]["14"], 1)
        self.assertNotIn("14", provider.categories["Episode"])
        self.assertNotIn("14", provider.tv_category_choices)

    def test_unknown_and_empty_restore_defaults(self):
        provider = Provider()
        provider.set_tv_categories(["999", "nope"])
        self.assertEqual(provider.tv_categories, DEFAULT_TV_CATEGORIES)
        provider.set_tv_categories("")
        self.assertEqual(provider.tv_categories, DEFAULT_TV_CATEGORIES)
        provider.set_tv_categories(["7", "7", "104", "14", "999"])
        self.assertEqual(provider.tv_categories, "7,104")
        self.assertEqual(provider.categories["Episode"], {"7": 1, "104": 1})
        self.assertEqual(provider.categories["Season"], {"14": 1})
        self.assertEqual(provider.categories["RSS"]["14"], 1)

    def test_apply_write_round_trip_does_not_stringify_categories_dict(self):
        provider = Provider()
        provider.set_tv_categories("7,34,14")
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_provider_section(cfg, "torrentday", _provider_to_section(provider))
        section = cfg["PROVIDERS"]["torrentday"]
        self.assertEqual(section.get("tv_categories"), "7,34")
        self.assertNotIsInstance(section.get("categories"), str)
        self.assertNotEqual(section.get("categories"), "7,34")

        other = Provider()
        other.tv_categories = DEFAULT_TV_CATEGORIES
        _apply_provider_options(cfg, other)
        self.assertEqual(other.tv_categories, "7,34")
        self.assertEqual(other.categories["Episode"], {"7": 1, "34": 1})
        self.assertEqual(other.categories["Season"], {"14": 1})
        self.assertEqual(other.categories["RSS"]["14"], 1)
