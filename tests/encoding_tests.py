# coding=utf-8
import unittest
import sys, os.path

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex

sickbeard.SYS_ENCODING = 'UTF-8'

class EncodingTests(unittest.TestCase):
    def test_encoding(self):
        strings = [u'Les Enfants De La Télé']

        for s in strings:
            try:
                x = ek.ss(s)
                assert isinstance(x, unicode)
            except Exception, e:
                ex(e)

if __name__ == "__main__":
    print "=================="
    print "STARTING - ENCODING TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(EncodingTests)
    unittest.TextTestRunner(verbosity=2).run(suite)