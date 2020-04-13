"""unit tests module for ndg.httpsclient.utils module

PyOpenSSL utility to make a httplib-like interface suitable for use with 
urllib2
"""
__author__ = "P J Kershaw (STFC)"
__date__ = "06/01/12"
__copyright__ = "(C) 2012 Science and Technology Facilities Council"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id$'
import unittest
import os

from OpenSSL import SSL

from ndg.httpsclient.test import Constants
from ndg.httpsclient.utils import (Configuration, fetch_from_url, open_url,
                                   _should_use_proxy)


class TestUtilsModule(unittest.TestCase):
    '''Test ndg.httpsclient.utils module'''

    def test01_configuration(self):
        config = Configuration(SSL.Context(SSL.TLSv1_2_METHOD), True)
        self.assertTrue(config.ssl_context)
        self.assertEqual(config.debug, True)

    def test02_fetch_from_url(self):
        config = Configuration(SSL.Context(SSL.TLSv1_2_METHOD), True)
        res = fetch_from_url(Constants.TEST_URI, config)
        self.assertTrue(res)
        
    def test03_open_url(self):
        config = Configuration(SSL.Context(SSL.TLSv1_2_METHOD), True)
        res = open_url(Constants.TEST_URI, config)
        self.assertEqual(res[0], 200, 
                         'open_url for %r failed' % Constants.TEST_URI)
        
    def test04__should_use_proxy(self):
        if 'no_proxy' in os.environ:
            no_proxy = os.environ['no_proxy']
            del os.environ['no_proxy']
        else:
            no_proxy = None
               
        self.assertTrue(_should_use_proxy(Constants.TEST_URI), 
                        'Expecting use proxy = True')
        
        os.environ['no_proxy'] = 'localhost,localhost.localdomain'
        self.assertFalse(_should_use_proxy(Constants.TEST_URI), 
                         'Expecting use proxy = False')
        
        if no_proxy is not None:
            os.environ['no_proxy'] = no_proxy
        else:
            del os.environ['no_proxy']
    

if __name__ == "__main__":
    unittest.main()