import unittest

import sickchill.oldbeard.providers
from sickchill import settings
from sickchill.oldbeard import common as common
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
        show.saveToDB()
        settings.showList.append(show)

        for ep_number in cur_data["e"]:
            episode = TVEpisode(show, cur_data["s"], ep_number)
            episode.status = common.WANTED

            # We aren't updating scene numbers, so fake it here
            episode.scene_season = cur_data["s"]
            episode.scene_episode = ep_number

            episode.saveToDB()

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
                if not word.lower() in title.lower():
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


if __name__ == "__main__":
    print("==================")
    print("STARTING - Search TESTS")
    print("==================")
    print("######################################################################")
    # create the test methods
    for forceSearch in (True, False):
        for name, data in TESTS.items():
            filename = name.replace(" ", "_")

            for provider in sickchill.oldbeard.providers.sortedProviderList():
                if provider.provider_type == GenericProvider.TORRENT:
                    if forceSearch:
                        test_name = "test_manual_{0}_{1}_{2}".format(filename, data["tvdbid"], provider.name)
                    else:
                        test_name = "test_{0}_{1}_{2}".format(filename, data["tvdbid"], provider.name)
                    test = generator(data, name, provider)
                    setattr(SearchTest, test_name, test)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(SearchTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
