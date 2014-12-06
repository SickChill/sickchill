# coding=utf-8
import unittest
import sys, os.path

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import sickbeard
from sickbeard import encodingKludge as ek
from sickbeard.exceptions import ex

sickbeard.SYS_ENCODING = 'UTF-8'

DEBUG = VERBOSE = False

class EncodingTests(unittest.TestCase):
    def test_encoding(self):
        strings = ['Les Enfants De La Télé', u'\x89']

        for s in strings:
            try:
                print ek.ss(s)
            except Exception, e:
                print ex(e)

if __name__ == "__main__":
    print "=================="
    print "STARTING - Encoding TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(EncodingTests)