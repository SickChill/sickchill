import unittest
#import test_lib as test
import sys, os.path

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import sickbeard
from encodingKludge import toUnicode
from sickbeard.exceptions import ex

sickbeard.SYS_ENCODING = 'UTF-8'

DEBUG = VERBOSE = False

class EncodingTests(unittest.TestCase):
    def test_encoding(self):
        s = u'\x89'
        try:
            print toUnicode(s).encode('utf-8', 'xmlcharrefreplace')
        except Exception, e:
            print ex(e)

if __name__ == "__main__":
    print "=================="
    print "STARTING - Encoding TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(EncodingTests)