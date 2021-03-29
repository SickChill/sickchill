"""
Test snatching
"""

import unittest

import sickchill.oldbeard.providers
from sickchill import settings
from sickchill.oldbeard import common as common, search as search
from sickchill.tv import TVEpisode, TVShow
from tests import conftest

TESTS = {
    "Dexter": {
        "a": 1,
        "q": common.HD,
        "s": 5,
        "e": [7],
        "b": "Dexter.S05E07.720p.BluRay.X264-REWARD",
        "i": ["Dexter.S05E07.720p.BluRay.X264-REWARD", "Dexter.S05E07.720p.X264-REWARD"],
    },
    "House": {
        "a": 1,
        "q": common.HD,
        "s": 4,
        "e": [5],
        "b": "House.4x5.720p.BluRay.X264-REWARD",
        "i": ["Dexter.S05E04.720p.X264-REWARD", "House.4x5.720p.BluRay.X264-REWARD"],
    },
    "Hells Kitchen": {
        "a": 1,
        "q": common.SD,
        "s": 6,
        "e": [14, 15],
        "b": "Hells.Kitchen.s6e14e15.HDTV.XviD-ASAP",
        "i": ["Hells.Kitchen.S06E14.HDTV.XviD-ASAP", "Hells.Kitchen.6x14.HDTV.XviD-ASAP", "Hells.Kitchen.s6e14e15.HDTV.XviD-ASAP"],
    },
}


def _create_fake_xml(items):
    """
    Create fake xml

    :param items:
    :return:
    """
    xml = '<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:newznab="http://www.newznab.com/DTD/2010/feeds/attributes/" encoding="utf-8"><channel>'  # noqa: E501
    for item in items:
        xml += "<item><title>" + item + "</title>\n"
        xml += "<link>http://fantasy.com/" + item + "</link></item>"
    xml += "</channel></rss>"
    return xml


search_items = []


class SearchTest(conftest.SickChillTestDBCase):
    """
    Perform search tests
    """

    @staticmethod
    def _fake_get_url(url, headers=None):
        """
        Fake getting a url

        :param url:
        :param headers:
        :return:
        """
        _ = url, headers
        return _create_fake_xml(search_items)

    @property
    def _fake_is_active(self):
        """
        Fake is active
        """
        return True

    def __init__(self, something):
        """
        Initialize tests

        :param something:
        :return:
        """

        for provider in sickchill.oldbeard.providers.sortedProviderList():
            provider.get_url = self._fake_get_url
            provider.is_active = self._fake_is_active

        super().__init__(something)


def generator(tvdb_id, show_name, cur_data, force_search):
    """
    Generate tests

    :param tvdb_id:
    :param show_name:
    :param cur_data:
    :param force_search:
    :return:
    """

    def do_test():
        """
        Test to perform
        """
        global search_items
        search_items = cur_data["i"]
        show = TVShow(1, tvdb_id)
        show.name = show_name
        show.quality = cur_data["q"]
        show.saveToDB()
        settings.showList.append(show)
        episode = None

        for epNumber in cur_data["e"]:
            episode = TVEpisode(show, cur_data["s"], epNumber)
            episode.status = common.WANTED
            episode.saveToDB()

        best_result = search.searchProviders(show, episode.episode, force_search)
        if not best_result:
            assert cur_data["b"] == best_result

        assert cur_data["b"] == best_result.name  # first is expected, second is chosen one

    return do_test


if __name__ == "__main__":
    print("==================")
    print("STARTING - Snatch TESTS")
    print("==================")
    print("######################################################################")
    # create the test methods
    cur_tvdb_id = 1
    for forceSearch in (True, False):
        for name, data in TESTS.items():
            if not data["a"]:
                continue
            filename = name.replace(" ", "_")
            if forceSearch:
                test_name = "test_manual_{0}_{1}".format(filename, cur_tvdb_id)
            else:
                test_name = "test_{0}_{1}".format(filename, cur_tvdb_id)

            test = generator(cur_tvdb_id, name, data, forceSearch)
            setattr(SearchTest, test_name, test)
            cur_tvdb_id += 1

    suite = unittest.TestLoader().loadTestsFromTestCase(SearchTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
