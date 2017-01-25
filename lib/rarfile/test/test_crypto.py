"""Crypto tests.
"""

from __future__ import division, print_function

from binascii import unhexlify

from nose.tools import *

import rarfile

try:
    from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
    from cryptography.hazmat.backends import default_backend
    def aes_encrypt(key, iv, data):
        ciph = Cipher(algorithms.AES(key), modes.CBC(iv), default_backend())
        enc = ciph.encryptor()
        return enc.update(data)
except ImportError:
    pass

if rarfile._have_crypto:
    def test_aes128_cbc():
        data = b'0123456789abcdef' * 2
        key = b'\x02' * 16
        iv = b'\x80' * 16

        #encdata = aes_encrypt(key, iv, data)
        encdata = unhexlify('4b0d438b4a1b972bd4ab81cd64674dcce4b0158090fbe616f455354284d53502')

        ctx = rarfile.AES_CBC_Decrypt(key, iv)
        eq_(ctx.decrypt(encdata), data)

    def test_aes256_cbc():
        data = b'0123456789abcdef' * 2
        key = b'\x52' * 32
        iv = b'\x70' * 16

        #encdata = aes_encrypt(key, iv, data)
        encdata = unhexlify('24988f387592e4d95b6eaab013137a221f81b25aa7ecde0ef4f4d7a95f92c250')

        ctx = rarfile.AES_CBC_Decrypt(key, iv)
        eq_(ctx.decrypt(encdata), data)

