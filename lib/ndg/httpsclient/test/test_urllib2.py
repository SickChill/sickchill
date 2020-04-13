"""unit tests module for ndg.httpsclient.urllib2_build_opener module

PyOpenSSL utility to make a httplib-like interface suitable for use with 
urllib2
"""
__author__ = "P J Kershaw (STFC)"
__date__ = "06/01/12"
__copyright__ = "(C) 2012 Science and Technology Facilities Council"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id$'
import sys

if sys.version_info[0] > 2:
    from urllib.error import URLError as URLError
else:
    from urllib2 import URLError as URLError
    
import unittest

from OpenSSL import SSL
from ndg.httpsclient.test import Constants
from ndg.httpsclient.urllib2_build_opener import build_opener
from ndg.httpsclient.ssl_peer_verification import ServerSSLCertVerification


class Urllib2TestCase(unittest.TestCase):
    """Unit tests for urllib2 functionality"""
    
    def test01_urllib2_build_opener(self):     
        opener = build_opener()
        self.assertTrue(opener)

    def test02_open(self):
        opener = build_opener()
        res = opener.open(Constants.TEST_URI)
        self.assertTrue(res)
        print("res = %s" % res.read())

    # Skip this test for remote service as it can take a long time to timeout
    @unittest.skipIf(Constants.HOSTNAME != 'localhost', 'Skip non-local host')
    def test03_open_fails_unknown_loc(self):
        opener = build_opener()
        self.assertRaises(URLError, opener.open, Constants.TEST_URI2)
        
    def test04_open_peer_cert_verification_fails(self):
        # Explicitly set empty CA directory to make verification fail
        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        verify_callback = lambda conn, x509, errnum, errdepth, preverify_ok: \
            preverify_ok 
            
        ctx.set_verify(SSL.VERIFY_PEER, verify_callback)
        ctx.load_verify_locations(None, './')
        opener = build_opener(ssl_context=ctx)
        self.assertRaises(SSL.Error, opener.open, Constants.TEST_URI)
      
    def test05_open_with_subj_alt_names_verification(self):
        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
                
        # Set wildcard hostname for subject alternative name matching - 
        # setting a minimum of two name components for hostname
        split_hostname = Constants.HOSTNAME.split('.', 1)
        if len(split_hostname) > 1:
            _hostname = '*.' + split_hostname[-1]
        else:
            _hostname = Constants.HOSTNAME
            
        server_ssl_verify = ServerSSLCertVerification(hostname=_hostname)
        verify_callback_ = server_ssl_verify.get_verify_server_cert_func()
        ctx.set_verify(SSL.VERIFY_PEER, verify_callback_)
        
        # Set default verify paths if testing with peer that has corresponding
        # CA cert in bundle provided with the OS.  In this case, load verify
        # locations is not needed.
        #ctx.set_default_verify_paths()
        
        ctx.set_verify_depth(9)
        
        # Set correct location for CA certs to verify with
        ctx.load_verify_locations(None, Constants.CACERT_DIR)
                            
        opener = build_opener(ssl_context=ctx)
        res = opener.open(Constants.TEST_URI)
        self.assertTrue(res)
        print("res = %s" % res.read())
                  
        
if __name__ == "__main__":
    unittest.main()
