"""Anime format modes: 0 standard, 1 absolute, 2 anime SxxExx."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sickchill.oldbeard.common import ANIME_ABSOLUTE, ANIME_NONE, ANIME_SEASON_EPISODE, parse_anime_form, parse_anime_mode, uses_absolute_numbering
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.tv import TVEpisode, TVShow


def _episode(anime_mode: int, scene: bool = False):
    show = SimpleNamespace(
        anime=anime_mode,
        air_by_date=False,
        sports=False,
        scene=scene,
    )
    return SimpleNamespace(
        show=show,
        scene_season=2,
        scene_episode=3,
        scene_absolute_number=265,
        naming_pattern=lambda pattern: pattern,
    )


class TestAnimeSxxExxMode(unittest.TestCase):
    def test_is_anime_true_for_mode_1_and_2(self):
        self.assertFalse(TVShow.is_anime.fget(SimpleNamespace(anime=ANIME_NONE)))
        self.assertTrue(TVShow.is_anime.fget(SimpleNamespace(anime=ANIME_ABSOLUTE)))
        self.assertTrue(TVShow.is_anime.fget(SimpleNamespace(anime=ANIME_SEASON_EPISODE)))

    def test_uses_absolute_numbering_only_mode_1(self):
        self.assertFalse(uses_absolute_numbering(SimpleNamespace(anime=ANIME_NONE)))
        self.assertTrue(uses_absolute_numbering(SimpleNamespace(anime=ANIME_ABSOLUTE)))
        self.assertFalse(uses_absolute_numbering(SimpleNamespace(anime=ANIME_SEASON_EPISODE)))

    def test_parse_anime_mode_accepts_0_1_2(self):
        self.assertEqual(parse_anime_mode(0), ANIME_NONE)
        self.assertEqual(parse_anime_mode("1"), ANIME_ABSOLUTE)
        self.assertEqual(parse_anime_mode(ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)

    def test_parse_anime_mode_invalid_keeps_fallback(self):
        self.assertEqual(parse_anime_mode("9", fallback=ANIME_ABSOLUTE), ANIME_ABSOLUTE)
        self.assertEqual(parse_anime_mode("nope", fallback=ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)
        self.assertEqual(parse_anime_mode(None, fallback=ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)
        self.assertEqual(parse_anime_mode("", fallback=ANIME_ABSOLUTE), ANIME_ABSOLUTE)

    def test_parse_anime_form_checkbox_and_radios(self):
        self.assertEqual(parse_anime_form(False, ANIME_SEASON_EPISODE), ANIME_NONE)
        self.assertEqual(parse_anime_form(True, ANIME_ABSOLUTE), ANIME_ABSOLUTE)
        self.assertEqual(parse_anime_form(True, ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)
        self.assertEqual(parse_anime_form(True, "9", fallback=ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)
        self.assertEqual(parse_anime_form(True, None, fallback=ANIME_NONE), ANIME_ABSOLUTE)
        self.assertEqual(parse_anime_form(True, ANIME_NONE, fallback=ANIME_SEASON_EPISODE), ANIME_SEASON_EPISODE)

    @patch("sickchill.providers.GenericProvider.all_possible_show_names", return_value=["Show.Name"])
    def test_episode_search_strings_by_mode(self, _names):
        provider = GenericProvider("test")

        mode0 = next(iter(provider.get_episode_search_strings(_episode(ANIME_NONE))[0]["Episode"]))
        self.assertIn("S02E03", mode0)
        self.assertNotIn("265", mode0)
        self.assertFalse(TVShow.is_anime.fget(_episode(ANIME_NONE).show))

        mode1 = provider.get_episode_search_strings(_episode(ANIME_ABSOLUTE))[0]["Episode"]
        self.assertTrue(any("265" in item for item in mode1))
        self.assertFalse(any("S02E03" in item for item in mode1))
        self.assertTrue(TVShow.is_anime.fget(_episode(ANIME_ABSOLUTE).show))

        two_digit = _episode(ANIME_ABSOLUTE)
        two_digit.scene_absolute_number = 65
        mode1_short = provider.get_episode_search_strings(two_digit)[0]["Episode"]
        self.assertTrue(any("065" in item for item in mode1_short))
        self.assertTrue(any(item.endswith("65") and "065" not in item for item in mode1_short))

        mode2 = next(iter(provider.get_episode_search_strings(_episode(ANIME_SEASON_EPISODE))[0]["Episode"]))
        self.assertIn("S02E03", mode2)
        self.assertNotIn("265", mode2)
        self.assertTrue(TVShow.is_anime.fget(_episode(ANIME_SEASON_EPISODE).show))

    @patch("sickchill.providers.GenericProvider.all_possible_show_names", return_value=["Show.Name"])
    def test_season_search_strings_by_mode(self, _names):
        provider = GenericProvider("test")

        mode1 = next(iter(provider.get_season_search_strings(_episode(ANIME_ABSOLUTE))[0]["Season"]))
        self.assertIn("Season", mode1)
        self.assertNotIn("S02", mode1)

        mode2 = next(iter(provider.get_season_search_strings(_episode(ANIME_SEASON_EPISODE))[0]["Season"]))
        self.assertIn("S02", mode2)
        self.assertNotIn("Season", mode2)

    def test_pretty_name_absolute_only_for_mode_1(self):
        self.assertEqual(TVEpisode.pretty_name.fget(_episode(ANIME_ABSOLUTE)), "%SN - %AB - %EN")
        self.assertEqual(TVEpisode.pretty_name.fget(_episode(ANIME_SEASON_EPISODE)), "%SN - S%0SE%0E - %EN")
        self.assertEqual(TVEpisode.pretty_name.fget(_episode(ANIME_NONE)), "%SN - S%0SE%0E - %EN")
