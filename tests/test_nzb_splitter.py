"""NZB season-pack split constructs NZBDataSearchResult with provider and url."""

from __future__ import annotations

import unittest
from unittest import mock

from sickchill.oldbeard import nzbSplitter
from sickchill.providers.result_classes import NZBDataSearchResult


class SplitResultTests(unittest.TestCase):
    def test_split_result_constructs_nzbdata_with_provider_and_url(self):
        provider = mock.Mock()
        show = mock.Mock()
        episode = mock.Mock()
        show.get_episode.return_value = episode
        show.want_episode.return_value = True

        season_result = mock.Mock()
        season_result.url = "http://example/season.nzb"
        season_result.name = "Show.S01.WEB-DL"
        season_result.provider = provider
        season_result.show = show
        season_result.quality = 8

        parsed = mock.Mock()
        parsed.season_number = 1
        parsed.episode_numbers = [2]

        with mock.patch("sickchill.oldbeard.nzbSplitter.helpers.getURL", return_value=b"<nzb/>"):
            with mock.patch(
                "sickchill.oldbeard.nzbSplitter.get_season_nzbs",
                return_value=({"Show.S01E02.WEB-DL": ["file"]}, "http://www.newzbin.com/DTD/2003/nzb"),
            ):
                with mock.patch("sickchill.oldbeard.nzbSplitter.NameParser") as parser_cls:
                    with mock.patch("sickchill.oldbeard.nzbSplitter.create_nzb_string", return_value="<nzb/>"):
                        parser_cls.return_value.parse.return_value = parsed
                        results = nzbSplitter.split_result(season_result)

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], NZBDataSearchResult)
        self.assertIs(results[0].provider, provider)
        self.assertEqual(results[0].url, "http://example/season.nzb")
        self.assertIs(results[0].show, show)
        self.assertEqual(results[0].name, "Show.S01E02.WEB-DL")
        self.assertEqual(results[0].result_type, "nzbdata")
        self.assertEqual(results[0].extraInfo, ["<nzb/>"])
