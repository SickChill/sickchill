import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import sickchill.oldbeard.providers
from sickchill import settings
from sickchill.oldbeard import common as common
from sickchill.oldbeard.search import search_for_needed_episodes, search_providers
from sickchill.oldbeard.search_queue import DailySearchQueueItem
from sickchill.oldbeard.tvcache import TVCache
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.tv import TVEpisode, TVShow
from tests import conftest

TESTS = {
    "Game of Thrones": {
        "tvdbid": 121361,
        "s": 5,
        "e": [10],
        "s_strings": [{"Season": ["Game of Thrones S05"]}],
        "e_strings": [{"Episode": ["Game of Thrones S05E10"]}],
    }
}


class SearchTest(conftest.SickChillTestDBCase):
    """
    Test search
    """

    def __init__(self, something):
        super().__init__(something)


def generator(cur_data, cur_name, cur_provider):
    """
    Generate test

    :param cur_data:
    :param cur_name:
    :param cur_provider:
    :return:
    """

    def do_test(self):
        """
        Test to perform
        """
        show = TVShow(1, int(cur_data["tvdbid"]))
        show.name = cur_name
        show.quality = common.ANY | common.Quality.UNKNOWN | common.Quality.RAWHDTV
        show.save_to_db()
        settings.show_list.append(show)

        for ep_number in cur_data["e"]:
            episode = TVEpisode(show, cur_data["s"], ep_number)
            episode.status = common.WANTED

            # We aren't updating scene numbers, so fake it here
            episode.scene_season = cur_data["s"]
            episode.scene_episode = ep_number

            episode.save_to_db()

            cur_provider.show = show
            season_strings = cur_provider.get_season_search_strings(episode)
            episode_strings = cur_provider.get_episode_search_strings(episode)

            fail = False
            cur_string = ""
            for cur_string in season_strings, episode_strings:
                if not all([isinstance(cur_string, list), isinstance(cur_string[0], dict)]):
                    print("{0} is using a wrong string format!".format(cur_provider.name))
                    print(cur_string)
                    fail = True
                    continue

            if fail:
                continue

            try:
                assert season_strings == cur_data["s_strings"]
                assert episode_strings == cur_data["e_strings"]
            except AssertionError:
                print("{0} is using a wrong string format!".format(cur_provider.name))
                print(cur_string)
                continue

            search_strings = episode_strings[0]
            # search_strings.update(season_strings[0])
            # search_strings.update({"RSS":['']})

            # print(search_strings)

            if not cur_provider.public:
                continue

            items = cur_provider.search(search_strings)
            if not items:
                print("No results from cur_provider?")
                continue

            title, url = cur_provider._get_title_and_url(items[0])
            for word in show.name.split(" "):
                if word.lower() not in title.lower():
                    print("Show cur_name not in title: {0}. URL: {1}".format(title, url))
                    continue

            if not url:
                print("url is empty")
                continue

            quality = cur_provider.get_quality(items[0])
            size = cur_provider._get_size(items[0])

            if not show.quality & quality:
                print("Quality not in common.ANY, {0!r} {1}".format(quality, size))
                continue

    return do_test


def _episode(number, season=1):
    episode = MagicMock()
    episode.episode = number
    episode.season = season
    episode.scene_season = season
    return episode


def _provider(search_mode="season", search_fallback=False):
    provider = MagicMock()
    provider.name = "FakeProvider"
    provider.is_active = True
    provider.can_backlog = True
    provider.enable_backlog = True
    provider.anime_only = False
    provider.search_mode = search_mode
    provider.search_fallback = search_fallback
    provider.cache.update_cache = MagicMock()
    return provider


def _show():
    show = MagicMock()
    show.name = "Test Show"
    show.is_anime = False
    return show


class SearchFallbackTests(unittest.TestCase):
    def _run(self, provider, manual=False):
        episodes = [_episode(1), _episode(2)]
        with patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]):
            search_providers(_show(), episodes, manual=manual)
        return [call.args[2] for call in provider.find_search_results.call_args_list]

    def test_season_fallback_on_switches_to_episode_when_no_pack(self):
        provider = _provider(search_mode="season", search_fallback=True)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider), ["season", "episode"])

    def test_season_fallback_off_stays_on_season_when_no_pack(self):
        provider = _provider(search_mode="season", search_fallback=False)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider), ["season"])

    def test_season_fallback_on_switches_when_only_episode_cache_hits(self):
        provider = _provider(search_mode="season", search_fallback=True)

        def fake_find(_show, _episodes, search_mode, *_args):
            if search_mode == "season":
                return {1: [MagicMock(quality=1)]}
            return {}

        provider.find_search_results.side_effect = fake_find
        with patch("sickchill.oldbeard.search.pick_best_result", return_value=None):
            self.assertEqual(self._run(provider), ["season", "episode"])

    def test_season_fallback_off_does_not_switch_when_only_episode_cache_hits(self):
        provider = _provider(search_mode="season", search_fallback=False)
        provider.find_search_results.return_value = {1: [MagicMock(quality=1)]}
        with patch("sickchill.oldbeard.search.pick_best_result", return_value=None):
            self.assertEqual(self._run(provider), ["season"])

    def test_season_fallback_on_does_not_switch_when_pack_found(self):
        provider = _provider(search_mode="season", search_fallback=True)
        pack = MagicMock()
        pack.quality = 1
        provider.find_search_results.return_value = {common.SEASON_RESULT: [pack]}
        with patch("sickchill.oldbeard.search.pick_best_result", side_effect=[pack, None]):
            self.assertEqual(self._run(provider), ["season"])

    def test_season_fallback_on_switches_when_pack_not_selectable(self):
        provider = _provider(search_mode="season", search_fallback=True)
        pack = MagicMock()
        pack.quality = 1
        provider.find_search_results.return_value = {common.SEASON_RESULT: [pack]}
        with patch("sickchill.oldbeard.search.pick_best_result", return_value=None):
            self.assertEqual(self._run(provider), ["season", "episode"])

    def test_episode_fallback_on_switches_to_season_when_empty(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider), ["episode", "season"])

    def test_episode_fallback_off_stays_on_episode_when_empty(self):
        provider = _provider(search_mode="episode", search_fallback=False)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider), ["episode"])

    def test_episode_fallback_on_switches_when_only_some_episodes_found(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.find_search_results.return_value = {1: [MagicMock(quality=1)]}
        with patch("sickchill.oldbeard.search.pick_best_result", return_value=None):
            self.assertEqual(self._run(provider), ["episode", "season"])

    def test_episode_fallback_on_does_not_switch_when_all_episodes_found(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.find_search_results.return_value = {1: [MagicMock(quality=1)], 2: [MagicMock(quality=1)]}
        with patch("sickchill.oldbeard.search.pick_best_result", return_value=None):
            self.assertEqual(self._run(provider), ["episode"])

    def test_episode_fallback_on_manual_does_not_switch_to_season(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider, manual=True), ["episode"])

    def test_season_mode_manual_searches_that_episode(self):
        provider = _provider(search_mode="season", search_fallback=False)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider, manual=True), ["episode"])

    def test_season_mode_manual_with_fallback_stays_on_episode(self):
        provider = _provider(search_mode="season", search_fallback=True)
        provider.find_search_results.return_value = {}
        self.assertEqual(self._run(provider, manual=True), ["episode"])

    def test_daily_search_does_not_use_search_mode_or_fallback(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.enable_daily = True
        provider.can_daily = True
        provider.search_rss.return_value = {}

        show = _show()
        show.paused = False
        with (
            patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]),
            patch("sickchill.oldbeard.search.settings.show_list", [show]),
            patch("sickchill.oldbeard.search.settings.RANDOMIZE_PROVIDERS", False),
            patch("sickchill.oldbeard.search.wanted_episodes", return_value=[_episode(1)]),
        ):
            search_for_needed_episodes()

        provider.search_rss.assert_called()
        provider.find_search_results.assert_not_called()
        provider.find_propers.assert_not_called()

    def test_daily_search_processes_cached_propers_when_enabled(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.enable_daily = True
        provider.can_daily = True
        provider.search_rss.return_value = {}

        show = _show()
        show.paused = False
        with (
            patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]),
            patch("sickchill.oldbeard.search.settings.show_list", [show]),
            patch("sickchill.oldbeard.search.settings.RANDOMIZE_PROVIDERS", False),
            patch("sickchill.oldbeard.search.settings.DOWNLOAD_PROPERS", True),
            patch("sickchill.oldbeard.search.wanted_episodes", return_value=[_episode(1)]),
            patch("sickchill.oldbeard.properFinder.ProperFinder") as finder_cls,
        ):
            search_for_needed_episodes()

        finder_cls.return_value.process_cached_propers.assert_called_once_with([provider])
        provider.find_propers.assert_not_called()

    def test_daily_search_skips_cached_propers_when_disabled(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.enable_daily = True
        provider.can_daily = True
        provider.search_rss.return_value = {}

        show = _show()
        show.paused = False
        with (
            patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]),
            patch("sickchill.oldbeard.search.settings.show_list", [show]),
            patch("sickchill.oldbeard.search.settings.RANDOMIZE_PROVIDERS", False),
            patch("sickchill.oldbeard.search.settings.DOWNLOAD_PROPERS", False),
            patch("sickchill.oldbeard.search.wanted_episodes", return_value=[_episode(1)]),
            patch("sickchill.oldbeard.properFinder.ProperFinder") as finder_cls,
        ):
            search_for_needed_episodes()

        finder_cls.assert_not_called()
        provider.find_propers.assert_not_called()

    def test_daily_search_processes_cached_propers_with_no_wanted_episodes(self):
        provider = _provider(search_mode="episode", search_fallback=True)
        provider.enable_daily = True
        provider.can_daily = True

        show = _show()
        show.paused = False
        with (
            patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]),
            patch("sickchill.oldbeard.search.settings.show_list", [show]),
            patch("sickchill.oldbeard.search.settings.RANDOMIZE_PROVIDERS", False),
            patch("sickchill.oldbeard.search.settings.DOWNLOAD_PROPERS", True),
            patch("sickchill.oldbeard.search.wanted_episodes", return_value=[]),
            patch("sickchill.oldbeard.properFinder.ProperFinder") as finder_cls,
        ):
            search_for_needed_episodes()

        provider.cache.update_cache.assert_not_called()
        provider.search_rss.assert_not_called()
        finder_cls.return_value.process_cached_propers.assert_called_once_with([provider])
        provider.find_propers.assert_not_called()


class CacheListQualityFilterTests(unittest.TestCase):
    def test_manual_list_search_keeps_every_cached_quality(self):
        cache = TVCache(GenericProvider("QualityFilter"))
        episode = MagicMock()
        episode.show.indexerid = 7
        episode.season = 1
        episode.episode = 3
        episode.wantedQuality = [16]

        with (
            patch.object(cache, "get_db") as get_db,
            patch.object(cache, "_shows_by_indexer", return_value=({}, set())),
            patch.object(cache, "set_last_search"),
        ):
            get_db.return_value.mass_action.return_value = []
            cache.find_needed_episodes([episode], manual_search=True)
            manual_sql = get_db.return_value.mass_action.call_args[0][0][0][0]
            get_db.return_value.mass_action.reset_mock()
            cache.find_needed_episodes([episode], manual_search=False)
            daily_sql = get_db.return_value.mass_action.call_args[0][0][0][0]

        self.assertNotIn("quality IN", manual_sql)
        self.assertIn("quality IN (16)", daily_sql)


class CacheReleaseCollapseTests(unittest.TestCase):
    def test_collapse_keeps_newest_url_for_one_release(self):
        older = {
            "provider": "jackett",
            "indexerid": 7,
            "season": 8,
            "episodes": "|26|",
            "name": "Paw.Patrol.S08E26.WEBRip.x264-PHOENiX",
            "url": "http://192.168.1.34:9117/dl/1337x/?path=old",
            "time": 10,
            "seeders": 50,
        }
        newer = dict(older)
        newer["url"] = "http://192.168.1.34:9117/dl/1337x/?path=new"
        newer["time"] = 20
        newer["seeders"] = 1
        other_episode = dict(older)
        other_episode["name"] = "Paw.Patrol.S08E25.WEBRip.x264-PHOENiX"
        other_episode["episodes"] = "|25|"
        other_episode["url"] = "http://192.168.1.34:9117/dl/1337x/?path=e25"
        other_episode["time"] = 5

        kept = TVCache._collapse_cache_rows([older, newer, other_episode, dict(newer)])
        self.assertCountEqual(
            [row["url"] for row in kept],
            [
                "http://192.168.1.34:9117/dl/1337x/?path=new",
                "http://192.168.1.34:9117/dl/1337x/?path=e25",
            ],
        )

    def test_collapse_prefers_seeders_when_time_matches(self):
        quiet = {
            "provider": "jackett",
            "indexerid": "7",
            "season": "8",
            "episodes": "|26|",
            "name": "Same.Release",
            "url": "http://example/quiet",
            "time": 20,
            "seeders": 1,
        }
        busy = dict(quiet)
        busy["url"] = "http://example/busy"
        busy["indexerid"] = 7
        busy["season"] = 8
        busy["seeders"] = 9

        kept = TVCache._collapse_cache_rows([quiet, busy])
        self.assertEqual([row["url"] for row in kept], ["http://example/busy"])


class LiveReleaseUrlTests(unittest.TestCase):
    def test_fresh_url_stays_selectable_when_cache_has_the_same_release(self):
        stale = SimpleNamespace(name="Show.S01E01", url="http://jackett/old")
        fresh = SimpleNamespace(name="Show.S01E01", url="http://jackett/new")
        other = SimpleNamespace(name="Show.S01E02", url="http://jackett/e2")
        cache_list = [({"name": "Show.S01E01", "url": "http://jackett/new"}, {"url": "http://jackett/new"})]

        kept = GenericProvider._drop_stale_cached_urls({1: [stale, fresh], 2: [other]}, cache_list)

        self.assertEqual([item.url for item in kept[1]], ["http://jackett/new"])
        self.assertEqual([item.url for item in kept[2]], ["http://jackett/e2"])

    def test_stale_url_stays_when_the_live_result_was_not_accepted(self):
        stale = SimpleNamespace(name="Show.S01E01", url="http://jackett/old")
        cache_list = [({"name": "Show.S01E01", "url": "http://jackett/new"}, {"url": "http://jackett/new"})]

        kept = GenericProvider._drop_stale_cached_urls({1: [stale]}, cache_list)

        self.assertEqual([item.url for item in kept[1]], ["http://jackett/old"])

    def test_multi_episode_live_url_covers_the_cached_first_episode(self):
        stale = SimpleNamespace(name="Show.S01E01E02", url="http://jackett/old")
        fresh = SimpleNamespace(name="Show.S01E01E02", url="http://jackett/new")
        cache_list = [({"name": "Show.S01E01E02", "url": "http://jackett/new"}, {"url": "http://jackett/new"})]

        kept = GenericProvider._drop_stale_cached_urls({1: [stale], common.MULTI_EP_RESULT: [fresh]}, cache_list)

        self.assertEqual([item.url for item in kept[1]], [])
        self.assertEqual([item.url for item in kept[common.MULTI_EP_RESULT]], ["http://jackett/new"])


class CacheEpisodeLookupTests(unittest.TestCase):
    def test_lookup_matches_each_requested_episode(self):
        cache = TVCache(GenericProvider("Lookup"))
        show = MagicMock()
        show.indexerid = 7
        show.is_anime = False
        catalog = {}

        def get_episode(season, episode, *args, **kwargs):
            key = (int(season), int(episode))
            if key not in catalog:
                item = MagicMock()
                item.season = key[0]
                item.episode = key[1]
                item.show = show
                catalog[key] = item
            return catalog[key]

        show.get_episode.side_effect = get_episode
        show.want_episode.return_value = True
        show.load_episode_statuses.side_effect = lambda pairs: {(int(season), int(number)): 3 for season, number in pairs}
        cache.provider.get_result = lambda episodes, url: SimpleNamespace(episodes=list(episodes), url=url)

        rows = [
            self._row(cache, "zero", "http://example/0", "|0|"),
            self._row(cache, "one", "http://example/1", "|1|"),
            self._row(cache, "pack", "http://example/pack", "|0|1|2|"),
        ]

        def select(_sql, params):
            token = params[3].strip("%")
            return [row for row in rows if token in row["episodes"] and int(row["season"]) == int(params[2])]

        db = MagicMock()
        db.select.side_effect = select
        db.mass_action.side_effect = lambda queries, fetchall=True: [select(sql, params) for sql, params in queries]

        episode0 = show.get_episode(1, 0)
        episode1 = show.get_episode(1, 1)
        episode2 = show.get_episode(1, 2)

        with (
            patch.object(cache, "get_db", return_value=db),
            patch.object(cache, "_shows_by_indexer", return_value=({7: show}, set())),
            patch.object(cache, "set_last_search"),
            patch("sickchill.oldbeard.tvcache.show_name_helpers.filter_bad_releases", return_value=True),
        ):
            by_zero = cache.find_needed_episodes([episode0])
            by_one = cache.find_needed_episodes([episode1])
            with self.assertLogs("sickchill", level="INFO") as logged:
                by_pack = cache.find_needed_episodes([episode0, episode1, episode2])
            cached_for_one = cache.search_cache(episode1)

        self.assertCountEqual([item.name for item in by_zero[episode0]], ["zero", "pack"])
        self.assertNotIn(episode1, by_zero)
        self.assertCountEqual([item.name for item in by_one[episode1]], ["one", "pack"])
        self.assertNotIn(episode0, by_one)
        self.assertCountEqual([item.name for item in by_pack[episode0]], ["zero", "pack"])
        self.assertCountEqual([item.name for item in by_pack[episode1]], ["one", "pack"])
        self.assertCountEqual([item.name for item in by_pack[episode2]], ["pack"])
        self.assertCountEqual([item.name for item in cached_for_one], ["one", "pack"])
        self.assertCountEqual(
            logged.output,
            [
                "INFO:sickchill:Found result zero at http://example/0",
                "INFO:sickchill:Found result one at http://example/1",
                "INFO:sickchill:Found result pack at http://example/pack",
            ],
        )

    @staticmethod
    def _row(cache, name, url, episodes):
        return {
            "provider": cache.provider_id,
            "indexerid": 7,
            "season": 1,
            "episodes": episodes,
            "name": name,
            "url": url,
            "time": 10,
            "seeders": 1,
            "quality": 4,
            "release_group": "G",
            "version": 1,
        }


class DailyReleaseSubmissionTests(unittest.TestCase):
    def test_cached_two_episode_release_is_submitted_once(self):
        cache = TVCache(GenericProvider("DailyPack"))
        show = MagicMock()
        show.indexerid = 7
        show.paused = False
        show.is_anime = False
        catalog = {}

        class Episode(object):
            def __init__(self, season, number):
                self.season = season
                self.episode = number
                self.show = show
                self.wantedQuality = [4]

        def get_episode(season, episode, *args, **kwargs):
            key = (int(season), int(episode))
            if key not in catalog:
                catalog[key] = Episode(key[0], key[1])
            return catalog[key]

        show.get_episode.side_effect = get_episode
        show.want_episode.return_value = True
        show.load_episode_statuses.side_effect = lambda pairs: {(int(season), int(number)): 3 for season, number in pairs}

        row = {
            "provider": cache.provider_id,
            "indexerid": 7,
            "season": 1,
            "episodes": "|1|2|",
            "name": "Show.S01E01E02",
            "url": "http://example/pack",
            "time": 10,
            "seeders": 1,
            "quality": 4,
            "release_group": "G",
            "version": 1,
        }

        def select(_sql, params):
            token = params[3].strip("%")
            return [row] if token in row["episodes"] and int(row["season"]) == int(params[2]) else []

        db = MagicMock()
        db.select.side_effect = select
        db.mass_action.side_effect = lambda queries, fetchall=True: [select(sql, params) for sql, params in queries]
        episode1 = show.get_episode(1, 1)
        episode2 = show.get_episode(1, 2)
        provider = _provider()
        provider.enable_daily = True
        provider.can_daily = True
        provider.search_rss.side_effect = lambda episodes: cache.find_needed_episodes(episodes)

        with (
            patch.object(cache, "get_db", return_value=db),
            patch.object(cache, "_shows_by_indexer", return_value=({7: show}, set())),
            patch.object(cache, "set_last_search"),
            patch("sickchill.oldbeard.tvcache.show_name_helpers.filter_bad_releases", return_value=True),
            patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]),
            patch("sickchill.oldbeard.search.settings.show_list", [show]),
            patch("sickchill.oldbeard.search.settings.RANDOMIZE_PROVIDERS", False),
            patch("sickchill.oldbeard.search.settings.DOWNLOAD_PROPERS", False),
            patch("sickchill.oldbeard.search.wanted_episodes", return_value=[episode1, episode2]),
            patch("sickchill.oldbeard.search.pick_best_result", side_effect=lambda results, _show: results[0]),
            patch("sickchill.oldbeard.search_queue.settings.CPU_PRESET", "HIGH"),
            patch("sickchill.oldbeard.search_queue.time.sleep"),
            patch("sickchill.oldbeard.search_queue.search.snatch_episode", return_value=True) as snatch,
        ):
            selected = search_for_needed_episodes()
            DailySearchQueueItem().run()

        self.assertEqual([result.url for result in selected], ["http://example/pack"])
        self.assertCountEqual([episode.episode for episode in selected[0].episodes], [1, 2])
        self.assertEqual(snatch.call_count, 1)
        submitted = snatch.call_args.args[0]
        self.assertEqual(submitted.url, "http://example/pack")
        self.assertCountEqual([episode.episode for episode in submitted.episodes], [1, 2])


class EpisodeTextTests(unittest.TestCase):
    def test_episode_zero_is_kept_and_numbers_are_sorted(self):
        cache = TVCache(GenericProvider("EpisodeText"))
        show = SimpleNamespace(indexerid=7)

        zero = SimpleNamespace(season_number=1, episode_numbers=[0], show=show, quality=4, release_group="G", version=1)
        stored, _control = cache.add_cache_entry("Show.S01E00", "http://example/0", 1, 1, 0, parse_result=zero)
        self.assertEqual(stored["episodes"], "|0|")

        mixed = SimpleNamespace(season_number=1, episode_numbers=[10, 2, None, 2, 0], show=show, quality=4, release_group="G", version=1)
        stored, _control = cache.add_cache_entry("Show.S01", "http://example/mix", 1, 1, 0, parse_result=mixed)
        self.assertEqual(stored["episodes"], "|0|2|10|")


class SeasonModeCacheTests(unittest.TestCase):
    def test_season_mode_still_searches_when_every_episode_is_cached(self):
        provider = GenericProvider("CacheSeason")
        provider.cache = MagicMock()
        cache_hit = [MagicMock()]
        provider.search = MagicMock(return_value=[])
        provider.get_season_search_strings = MagicMock(return_value=[{"Season": {"Show S01"}}])

        show = MagicMock()
        show.is_anime = False
        episodes = [_episode(1), _episode(2)]
        provider.cache.find_needed_episodes.return_value = {episode: cache_hit for episode in episodes}

        results = provider.find_search_results(show, episodes, "season")

        provider.search.assert_called()
        self.assertEqual(provider.get_season_search_strings.call_count, 1)
        self.assertEqual(results[1], cache_hit)
        self.assertEqual(results[2], cache_hit)

    def test_episode_mode_still_searches_when_cache_covers_all(self):
        provider = GenericProvider("CacheEpisode")
        provider.cache = MagicMock()
        cache_hit = [MagicMock()]
        provider.search = MagicMock(return_value=[])
        provider.get_episode_search_strings = MagicMock(return_value=[{"Episode": {"Show S01E01"}}])

        show = MagicMock()
        show.is_anime = False
        episode = _episode(1)
        provider.cache.find_needed_episodes.return_value = {episode: cache_hit}
        results = provider.find_search_results(show, [episode], "episode")

        provider.search.assert_called()
        provider.get_episode_search_strings.assert_called()
        self.assertEqual(results[1], cache_hit)

    def test_episode_mode_omits_quality_tokens_for_manual(self):
        provider = GenericProvider("QualityEpisode")
        provider.cache = MagicMock()
        provider.cache.find_needed_episodes.return_value = {}
        provider.search = MagicMock(return_value=[])

        def fake_episode_strings(_episode, add_string=""):
            label = "Show S01E01"
            if add_string:
                label = f"{label} {add_string}"
            return [{"Episode": {label}}]

        provider.get_episode_search_strings = MagicMock(side_effect=fake_episode_strings)

        show = MagicMock()
        show.is_anime = False
        show.quality = common.Quality.FULLHDWEBDL
        provider.find_search_results(show, [_episode(1)], "episode", manual_search=True)

        self.assertEqual(provider.get_episode_search_strings.call_args.kwargs.get("add_string", ""), "")
        searched = provider.search.call_args[0][0]
        self.assertEqual(searched["Episode"], {"Show S01E01"})

    def test_episode_mode_omits_quality_tokens_for_backlog(self):
        provider = GenericProvider("QualityEpisodeBacklog")
        provider.cache = MagicMock()
        provider.cache.find_needed_episodes.return_value = {}
        provider.search = MagicMock(return_value=[])

        def fake_episode_strings(_episode, add_string=""):
            label = "Show S01E01"
            if add_string:
                label = f"{label} {add_string}"
            return [{"Episode": {label}}]

        provider.get_episode_search_strings = MagicMock(side_effect=fake_episode_strings)

        show = MagicMock()
        show.is_anime = False
        show.quality = common.Quality.FULLHDTV | common.Quality.FULLHDWEBDL | common.Quality.FULLHDBLURAY
        provider.find_search_results(show, [_episode(1)], "episode")

        self.assertEqual(provider.get_episode_search_strings.call_args.kwargs.get("add_string", ""), "")
        searched = provider.search.call_args[0][0]
        self.assertEqual(searched["Episode"], {"Show S01E01"})

    def test_season_mode_omits_quality_tokens_for_manual(self):
        provider = GenericProvider("QualitySeason")
        provider.cache = MagicMock()
        provider.cache.find_needed_episodes.return_value = {}
        provider.search = MagicMock(return_value=[])
        provider.get_season_search_strings = MagicMock(return_value=[{"Season": {"Show S01"}}])

        show = MagicMock()
        show.is_anime = False
        show.quality = common.Quality.HDTV | common.Quality.FULLHDWEBDL
        provider.find_search_results(show, [_episode(1), _episode(2)], "season", manual_search=True)

        searched = provider.search.call_args[0][0]
        self.assertEqual(searched["Season"], {"Show S01"})

    def test_season_mode_omits_quality_tokens_for_backlog(self):
        provider = GenericProvider("QualitySeasonBacklog")
        provider.cache = MagicMock()
        provider.cache.find_needed_episodes.return_value = {}
        provider.search = MagicMock(return_value=[])
        provider.get_season_search_strings = MagicMock(return_value=[{"Season": {"Show S01"}}])

        show = MagicMock()
        show.is_anime = False
        show.quality = common.Quality.FULLHDTV | common.Quality.FULLHDWEBDL | common.Quality.FULLHDBLURAY
        provider.find_search_results(show, [_episode(1), _episode(2)], "season")

        searched = provider.search.call_args[0][0]
        self.assertEqual(searched["Season"], {"Show S01"})


class ManualBacklogLiveSearchTests(unittest.TestCase):
    def test_manual_skips_rss_cache_update(self):
        provider = _provider(search_mode="episode")
        provider.find_search_results.return_value = {}
        with patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]):
            search_providers(_show(), [_episode(1)], manual=True)
        provider.cache.update_cache.assert_not_called()

    def test_backlog_still_updates_rss_cache(self):
        provider = _provider(search_mode="episode")
        provider.find_search_results.return_value = {}
        with patch("sickchill.oldbeard.providers.sorted_provider_list", return_value=[provider]):
            search_providers(_show(), [_episode(1)], manual=False)
        provider.cache.update_cache.assert_called()


if __name__ == "__main__":
    print("==================")
    print("STARTING - Search TESTS")
    print("==================")
    print("######################################################################")
    # create the test methods
    for forceSearch in (True, False):
        for name, data in TESTS.items():
            filename = name.replace(" ", "_")

            for provider in sickchill.oldbeard.providers.sorted_provider_list():
                if provider.provider_type == GenericProvider.TORRENT:
                    if forceSearch:
                        test_name = "test_manual_{0}_{1}_{2}".format(filename, data["tvdbid"], provider.name)
                    else:
                        test_name = "test_{0}_{1}_{2}".format(filename, data["tvdbid"], provider.name)
                    test = generator(data, name, provider)
                    setattr(SearchTest, test_name, test)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(SearchTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
