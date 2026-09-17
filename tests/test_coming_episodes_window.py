"""Schedule coming-episodes window must not drop next week's row on air day."""

from __future__ import annotations

import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from sickchill import settings
from sickchill.helper.common import try_int
from sickchill.oldbeard.common import UNAIRED, WANTED
from sickchill.oldbeard.network_timezones import sc_today
from sickchill.show.ComingEpisodes import ComingEpisodes
from sickchill.tv import TVShow


class ComingEpisodesSortTests(unittest.TestCase):
    def test_date_sort_uses_show_name_when_airtime_ties(self):
        key = ComingEpisodes.sorts["date"]
        earlier = {"snatchedsort": 1, "localtime": 10, "show_name": "Zebra", "episode": 1}
        tied_a = {"snatchedsort": 1, "localtime": 20, "show_name": "Alpha", "episode": 1}
        tied_b = {"snatchedsort": 1, "localtime": 20, "show_name": "Beta", "episode": 1}
        ordered = sorted([tied_b, earlier, tied_a], key=key)
        self.assertEqual([row["show_name"] for row in ordered], ["Zebra", "Alpha", "Beta"])

    def test_date_sort_groups_same_show_instead_of_interleaving_by_episode(self):
        # Regression: same airtime used to sort by episode only → Neagley E01, Slow Horses E01, Neagley E02…
        key = ComingEpisodes.sorts["date"]
        rows = [
            {"snatchedsort": 1, "localtime": 20, "show_name": "Neagley", "episode": 1},
            {"snatchedsort": 1, "localtime": 20, "show_name": "Slow Horses", "episode": 1},
            {"snatchedsort": 1, "localtime": 20, "show_name": "Neagley", "episode": 2},
            {"snatchedsort": 1, "localtime": 20, "show_name": "Last Seen", "episode": 3},
            {"snatchedsort": 1, "localtime": 20, "show_name": "Neagley", "episode": 3},
        ]
        ordered = sorted(rows, key=key)
        self.assertEqual(
            [(row["show_name"], row["episode"]) for row in ordered],
            [
                ("Last Seen", 3),
                ("Neagley", 1),
                ("Neagley", 2),
                ("Neagley", 3),
                ("Slow Horses", 1),
            ],
        )


class ComingEpisodesWindowTests(unittest.TestCase):
    def test_upper_bound_covers_soon_when_next_is_stale_today(self):
        today = sc_today().toordinal()
        next_week = (sc_today() + timedelta(days=7)).toordinal()
        # Stale cache: next_episode still today's ordinal after S01Ex left UNAIRED/WANTED
        stale_next = today
        upper = max(try_int(stale_next) or today, next_week)
        self.assertEqual(upper, next_week)
        # Next week's episode must fall inside the query window
        soon_ep = today + 7
        self.assertLessEqual(soon_ep, upper)

    def test_upper_bound_keeps_later_when_next_is_far(self):
        today = sc_today().toordinal()
        next_week = (sc_today() + timedelta(days=7)).toordinal()
        later = today + 21
        upper = max(try_int(later) or today, next_week)
        self.assertEqual(upper, later)

    def test_next_episode_refreshes_on_air_day(self):
        today = sc_today().toordinal()
        later = today + 7
        show = object.__new__(TVShow)
        show.indexerid = 12345
        show.next_airdate = today  # stale: pointed at today's cleared episode

        db = MagicMock()
        db.select.return_value = [{"airdate": later, "season": 1, "episode": 6}]

        with patch("sickchill.tv.db.DBConnection", return_value=db), patch("sickchill.tv.sc_today", return_value=sc_today()):
            result = TVShow.next_episode(show)

        self.assertEqual(result, later)
        db.select.assert_called_once()
        args = db.select.call_args[0]
        self.assertIn("airdate >= ?", args[0])
        self.assertEqual(args[1][0], 12345)
        self.assertEqual(args[1][2], UNAIRED)
        self.assertEqual(args[1][3], WANTED)


class ComingEpisodesQueryBoundTests(unittest.TestCase):
    @patch("sickchill.show.ComingEpisodes.DBConnection")
    def test_query_uses_at_least_next_week_upper_bound(self, db_cls):
        today = sc_today()
        today_ord = today.toordinal()
        next_week = (today + timedelta(days=7)).toordinal()

        show = MagicMock()
        show.indexerid = 99
        show.next_episode.return_value = today_ord  # stale today

        db = MagicMock()
        db.select.return_value = []
        db_cls.return_value = db

        saved_list = settings.show_list
        saved_missed = settings.COMING_EPS_MISSED_RANGE
        settings.show_list = [show]
        settings.COMING_EPS_MISSED_RANGE = 7
        try:
            ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, "date", False)
        finally:
            settings.show_list = saved_list
            settings.COMING_EPS_MISSED_RANGE = saved_missed

        self.assertTrue(db.select.called)
        params = db.select.call_args[0][1]
        # [indexerid, upper, recently, ...statuses]
        self.assertEqual(params[0], 99)
        self.assertEqual(params[1], next_week)


if __name__ == "__main__":
    unittest.main()
