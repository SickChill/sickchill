import unittest

import sickchill.logger
from sickchill import settings
from sickchill.oldbeard.providers import bitcannon, rarbg
from sickchill.tv import TVEpisode, TVShow
from tests import test_lib as test


class TorrentBasicTests(test.SickChillTestDBCase):
    """
    Test torrents
    """
    @classmethod
    def setUpClass(cls):
        cls.shows = []

        show = TVShow(1, 121361)
        show.name = "Italian Works"
        show.episodes = []
        episode = TVEpisode(show, 5, 10)
        episode.name = "Pines of Rome"
        episode.scene_season = 5
        episode.scene_episode = 10
        show.episodes.append(episode)
        cls.shows.append(show)

    def test_bitcannon(self):
        """
        Test bitcannon
        """
        provider = bitcannon.Provider()
        provider.custom_url = ""        # true testing requires a valid URL here (e.g., "http://localhost:3000/")
        provider.api_key = ""

        if provider.custom_url:

            search_strings_list = provider.get_episode_search_strings(self.shows[0].episodes[0])  # [{'Episode': ['Italian Works S05E10']}]
            for search_strings in search_strings_list:
                provider.search(search_strings)   # {'Episode': ['Italian Works S05E10']}

        return True

    @unittest.skip('Only run this manually')
    def test_search(self):
        """
        Test searching, using rarbg
        """
        settings.CPU_PRESET = 'LOW'
        provider = rarbg.Provider()
        results = provider.search({'Episode': ['The Mandalorian S01E08']})
        self.assertTrue(results)
        self.assertIn('Mandalorian', results[0]['title'])

        results = provider.search({'RSS': ['']})
        self.assertTrue(results)


if __name__ == "__main__":
    print("==================")
    print("STARTING - Torrent Basic TESTS")
    print("==================")
    print("######################################################################")

    def override_log(msg, *args, **kwargs):
        """Override the SickChill logger so we can see the debug output from providers"""
        _ = args, kwargs
        print(msg)

    sickchill.logger.info = override_log
    sickchill.logger.debug = override_log
    sickchill.logger.error = override_log
    sickchill.logger.warning = override_log

    SUITE = unittest.TestLoader().loadTestsFromTestCase(TorrentBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
