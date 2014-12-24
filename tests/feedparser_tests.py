import unittest
import sys
import os.path
import test_lib as test

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

from sickbeard.rssfeeds import RSSFeeds

class FeedParserTests(unittest.TestCase):
    def test_newznab(self):
        RSSFeeds().clearCache()
        result = RSSFeeds().getFeed('http://lolo.sickbeard.com/api?t=caps')
        self.assertTrue('entries' in result)
        self.assertTrue('feed' in result)
        self.assertTrue('categories' in result.feed)

if __name__ == "__main__":
    print "=================="
    print "STARTING - FEEDPARSER TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(FeedParserTests)
    testresults = unittest.TextTestRunner(verbosity=2).run(suite)

    # Return 0 if successful, 1 if there was a failure
    sys.exit(not testresults.wasSuccessful())