import sys, os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from sickbeard.providers.womble import provider as womble

class FeedParserTests(unittest.TestCase):
    # pylint: disable=W0212
    def test_womble(self):
        result = womble.cache.getRSSFeed('http://newshost.co.za/rss/?sec=tv-sd&fr=false')
        self.assertTrue('entries' in result)
        self.assertTrue('feed' in result)
        for item in result['entries'] or []:
            title, url = womble._get_title_and_url(item)
            self.assertTrue(title and url)

if __name__ == "__main__":
    print "=================="
    print "STARTING - FEEDPARSER TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(FeedParserTests)
    testresults = unittest.TextTestRunner(verbosity=2).run(suite)

    # Return 0 if successful, 1 if there was a failure
    sys.exit(not testresults.wasSuccessful())
