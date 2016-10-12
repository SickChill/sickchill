# coding=utf-8

"""
Test Feed Parser
"""

import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard.providers.womble import provider as womble


class FeedParserTests(unittest.TestCase):
    """
    Test feed parser
    """
    def test_womble(self):
        """
        Test womble
        """
        result = womble.cache.getRSSFeed(womble.urls['rss'], params={'sec': 'tv-sd', 'fr': 'false'})
        self.assertTrue('entries' in result)
        self.assertTrue('feed' in result)
        for item in result['entries'] or []:
            title, url = womble._get_title_and_url(item)     # pylint: disable=protected-access
            self.assertTrue(title and url)

if __name__ == "__main__":
    print "=================="
    print "STARTING - FEED PARSER TESTS"
    print "=================="
    print "######################################################################"
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FeedParserTests)
    TEST_RESULTS = unittest.TextTestRunner(verbosity=2).run(SUITE)

    # Return 0 if successful, 1 if there was a failure
    sys.exit(not TEST_RESULTS.wasSuccessful())
