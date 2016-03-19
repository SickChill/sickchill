"""Unit tests package for ndg_httpsclient

PyOpenSSL utility to make a httplib-like interface suitable for use with 
urllib2
"""
__author__ = "P J Kershaw (STFC)"
__date__ = "05/01/12"
__copyright__ = "(C) 2012 Science and Technology Facilities Council"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id$'
import os
import unittest
    
class Constants(object):
    '''Convenience base class from which other unit tests can extend.  Its
    sets the generic data directory path'''
    PORT = 4443
    PORT2 = 4444
    HOSTNAME = 'localhost'
    TEST_URI = 'https://{0!s}:{1:d}'.format(HOSTNAME, PORT)
    TEST_URI2 = 'https://{0!s}:{1:d}'.format(HOSTNAME, PORT2)

    UNITTEST_DIR = os.path.dirname(os.path.abspath(__file__))
    CACERT_DIR = os.path.join(UNITTEST_DIR, 'pki', 'ca')
    SSL_CERT_FILENAME = 'localhost.crt'
    SSL_CERT_FILEPATH = os.path.join(UNITTEST_DIR, 'pki', SSL_CERT_FILENAME)
    SSL_PRIKEY_FILENAME = 'localhost.key'
    SSL_PRIKEY_FILEPATH = os.path.join(UNITTEST_DIR, 'pki', SSL_PRIKEY_FILENAME)
