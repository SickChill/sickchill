import sys, os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import test_lib as test

from sickbeard.rssfeeds import RSSFeeds
from sickbeard.tvcache import TVCache
class FeedParserTests(unittest.TestCase):
    def test_womble(self):
        RSSFeeds().clearCache()
        result = RSSFeeds().getFeed('https://newshost.co.za/rss/?sec=tv-sd&fr=false')
        self.assertTrue('entries' in result)
        self.assertTrue('feed' in result)
        for item in result['entries']:
            self.assertTrue(TVCache._parseItem(item))

if __name__ == "__main__":
    print "=================="
    print "STARTING - FEEDPARSER TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(FeedParserTests)
    testresults = unittest.TextTestRunner(verbosity=2).run(suite)

    # Return 0 if successful, 1 if there was a failure
    sys.exit(not testresults.wasSuccessful())
