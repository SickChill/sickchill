"""
Test shows
"""


import unittest

from sickchill import settings
from sickchill.helper.exceptions import MultipleShowObjectsException
from sickchill.oldbeard.common import Quality
from sickchill.show.Show import Show
from sickchill.tv import TVShow


class ShowTests(unittest.TestCase):
    """
    Test shows
    """

    def test_find(self):
        """
        Test find tv shows by indexer_id
        """
        settings.QUALITY_DEFAULT = Quality.FULLHDTV

        settings.showList = []

        show123 = TestTVShow(0, 123)
        show456 = TestTVShow(0, 456)
        show789 = TestTVShow(0, 789)
        shows = [show123, show456, show789]
        shows_duplicate = shows + shows

        test_cases = {
            (False, None): None,
            (False, ""): None,
            (False, "123"): None,
            (False, 123): None,
            (False, 12.3): None,
            (True, None): None,
            (True, ""): None,
            (True, "123"): show123,
            (True, 123): show123,
            (True, 12.3): None,
            (True, 456): show456,
            (True, 789): show789,
        }

        unicode_test_cases = {
            (False, ""): None,
            (False, "123"): None,
            (True, ""): None,
            (True, "123"): show123,
        }

        for tests in test_cases, unicode_test_cases:
            for ((use_shows, indexer_id), result) in tests.items():
                if use_shows:
                    assert Show.find(shows, indexer_id) == result
                else:
                    assert Show.find(None, indexer_id) == result

        with self.assertRaises(MultipleShowObjectsException):
            Show.find(shows_duplicate, 456)

    def test_validate_indexer_id(self):
        """
        Tests if the indexer_id is valid and if so if it returns the right show
        """
        settings.QUALITY_DEFAULT = Quality.FULLHDTV

        settings.showList = []

        show123 = TestTVShow(0, 123)
        show456 = TestTVShow(0, 456)
        show789 = TestTVShow(0, 789)
        settings.showList = [
            show123,
            show456,
            show789,
        ]

        invalid_show_id = ("Invalid show ID", None)

        indexer_id_list = [None, "", "", "123", "123", "456", "456", "789", "789", 123, 456, 789, ["123", "456"], ["123", "456"], [123, 456]]
        results_list = [
            invalid_show_id,
            invalid_show_id,
            invalid_show_id,
            (None, show123),
            (None, show123),
            (None, show456),
            (None, show456),
            (None, show789),
            (None, show789),
            (None, show123),
            (None, show456),
            (None, show789),
            invalid_show_id,
            invalid_show_id,
            invalid_show_id,
        ]

        assert len(indexer_id_list) == len(results_list), "Number of parameters ({0:d}) and results ({1:d}) does not match".format(
            len(indexer_id_list), len(results_list))

        for (index, indexer_id) in enumerate(indexer_id_list):
            assert Show._validate_indexer_id(indexer_id) == results_list[index]


class TestTVShow(TVShow):
    """
    A test `TVShow` object that does not need DB access.
    """

    __test__ = False

    def __init__(self, indexer, indexer_id):
        super().__init__(indexer, indexer_id)

    def loadFromDB(self):
        """
        Override TVShow.loadFromDB to avoid DB access during testing
        """
        pass


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ShowTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
