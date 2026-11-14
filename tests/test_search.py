import unittest
from unittest.mock import MagicMock, patch

import sickchill.oldbeard.providers
from sickchill import settings
from sickchill.oldbeard import common as common
from sickchill.oldbeard.search import search_for_needed_episodes, search_providers
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


class SeasonModeCacheTests(unittest.TestCase):
    def test_season_mode_still_searches_when_every_episode_is_cached(self):
        provider = GenericProvider("CacheSeason")
        provider.cache = MagicMock()
        cache_hit = [MagicMock()]
        provider.cache.search_cache.return_value = cache_hit
        provider.search = MagicMock(return_value=[])
        provider.get_season_search_strings = MagicMock(return_value=[{"Season": {"Show S01"}}])

        show = MagicMock()
        show.is_anime = False
        episodes = [_episode(1), _episode(2)]

        results = provider.find_search_results(show, episodes, "season")

        provider.search.assert_called()
        self.assertEqual(provider.get_season_search_strings.call_count, 1)
        self.assertEqual(results[1], cache_hit)
        self.assertEqual(results[2], cache_hit)

    def test_episode_mode_still_searches_when_cache_covers_all(self):
        provider = GenericProvider("CacheEpisode")
        provider.cache = MagicMock()
        cache_hit = [MagicMock()]
        provider.cache.search_cache.return_value = cache_hit
        provider.search = MagicMock(return_value=[])
        provider.get_episode_search_strings = MagicMock(return_value=[{"Episode": {"Show S01E01"}}])

        show = MagicMock()
        show.is_anime = False
        results = provider.find_search_results(show, [_episode(1)], "episode")

        provider.search.assert_called()
        provider.get_episode_search_strings.assert_called()
        self.assertEqual(results[1], cache_hit)

    def test_episode_mode_omits_quality_tokens_for_manual(self):
        provider = GenericProvider("QualityEpisode")
        provider.cache = MagicMock()
        provider.cache.search_cache.return_value = []
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
        provider.cache.search_cache.return_value = []
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
        provider.cache.search_cache.return_value = []
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
        provider.cache.search_cache.return_value = []
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
