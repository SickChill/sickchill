"""
Test coming episodes
"""


import unittest

from sickchill.show.ComingEpisodes import ComingEpisodes


class ComingEpisodesTests(unittest.TestCase):
    """
    Test comping episodes
    """

    def test_get_categories(self):
        """
        Tests if get_categories returns the valid format and the right values
        """
        categories_list = [
            None,
            [],
            ["A", "B"],
            ["A", "B"],
            "",
            "A|B",
            "A|B",
        ]
        results_list = [[], [], ["A", "B"], ["A", "B"], [], ["A", "B"], ["A", "B"]]

        assert len(categories_list) == len(results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(categories_list), len(results_list))

        for (index, categories) in enumerate(categories_list):
            assert ComingEpisodes._get_categories(categories) == results_list[index]

    def test_get_categories_map(self):
        """
        Tests if get_categories_map returns the valid format and the right values
        """
        categories_list = [None, [], ["A", "B"], ["A", "B"]]
        results_list = [{}, {}, {"A": [], "B": []}, {"A": [], "B": []}]

        assert len(categories_list) == len(results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(categories_list), len(results_list))

        for (index, categories) in enumerate(categories_list):
            assert ComingEpisodes._get_categories_map(categories) == results_list[index]

    def test_get_sort(self):
        """
        Tests if get_sort returns the right sort of coming episode
        """
        test_cases = {
            None: "date",
            "": "date",
            "wrong": "date",
            "date": "date",
            "Date": "date",
            "network": "network",
            "NetWork": "network",
            "show": "show",
            "Show": "show",
        }

        unicode_test_cases = {
            "": "date",
            "wrong": "date",
            "date": "date",
            "Date": "date",
            "network": "network",
            "NetWork": "network",
            "show": "show",
            "Show": "show",
        }

        for tests in test_cases, unicode_test_cases:
            for (sort, result) in tests.items():
                assert ComingEpisodes._get_sort(sort) == result


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ComingEpisodesTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
