# coding=utf-8

"""
Test the SR API
"""

import unittest


class APITestEpisodes(unittest.TestCase):
    """
    Test episode commands for API

    This tests all episode related commands from the legacy api.
    """
    @unittest.skip('Not yet implemented')
    def test_episode(self):
        """
        Test getting detailed information about an episode using the legacy API.

        :return: None
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_episode_search(self):
        """
        Test searching for an episode using the legacy API.
        The response might take some time.
        :return: None
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_episode_set_status(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_episode_subtitle_search(self):
        pass


class APITestShows(unittest.TestCase):
    """
    Test shows commands for API
    """
    @unittest.skip('Not yet implemented')
    def test_shows(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_shows_stats(self):
        pass


class APITestShow(unittest.TestCase):
    """
    Test show commands for API
    """
    @unittest.skip('Not yet implemented')
    def test_show(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_add_existing(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_add_new(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_cache(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_delete(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_get_banner(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_get_fanart(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_get_network_logo(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_get_poster(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_get_quality(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_pause(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_refresh(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_season_list(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_seasons(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_set_quality(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_stats(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_show_update(self):
        pass


class APITestSickChill(unittest.TestCase):
    @unittest.skip('Not yet implemented')
    def test_sickchill(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_add_root_dir(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_check_scheduler(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_check_version(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_delete_root_dir(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_get_defaults(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_get_messages(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_get_root_dirs(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_pause_backlog(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_ping(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_restart(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_search_indexers(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_search_tvdb(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_search_tvrage(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_set_defaults(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_shutdown(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_sb_update(self):
        pass


class APITestHistory(unittest.TestCase):
    @unittest.skip('Not yet implemented')
    def test_history(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_history_clear(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_history_trim(self):
        pass


class APITestMisc(unittest.TestCase):
    @unittest.skip('Not yet implemented')
    def test_backlog(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_exceptions(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_failed(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_future(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_help(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_logs(self):
        pass

    @unittest.skip('Not yet implemented')
    def test_post_process(self):
        pass


TEST_CLASSES = {
    APITestEpisodes, APITestHistory, APITestMisc, APITestShow, APITestShows, APITestSickChill
}


def run_all():
    """
    Run all tests
    :return:
    """
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_all()
