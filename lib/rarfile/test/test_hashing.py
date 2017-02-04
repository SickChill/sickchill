"""Hashing tests.
"""

from __future__ import division, print_function

from binascii import unhexlify

from nose.tools import *

import rarfile

from rarfile import Blake2SP, CRC32Context, NoHashContext, tohex

def test_nohash():
    eq_(NoHashContext('').hexdigest(), None)
    eq_(NoHashContext('asd').hexdigest(), None)
    md = NoHashContext()
    md.update('asd')
    eq_(md.digest(), None)

def test_crc32():
    eq_(CRC32Context(b'').hexdigest(), '00000000')
    eq_(CRC32Context(b'Hello').hexdigest(), 'f7d18982')
    eq_(CRC32Context(b'Bye').hexdigest(), '4f7ad7d4')

    md = CRC32Context()
    md.update(b'He')
    md.update(b'll')
    md.update(b'o')
    eq_(md.hexdigest(), 'f7d18982')

def xblake2sp(xdata):
    data = unhexlify(xdata)
    md = Blake2SP()
    md.update(data)
    return md.hexdigest()

def xblake2sp_slow(xdata):
    data = unhexlify(xdata)
    md = Blake2SP()
    buf = memoryview(data)
    pos = 0
    while pos < len(buf):
        md.update(buf[pos : pos+3])
        pos += 3
    return md.hexdigest()


if rarfile._have_blake2:
    def test_blake2sp():
        eq_(Blake2SP(b'').hexdigest(), 'dd0e891776933f43c7d032b08a917e25741f8aa9a12c12e1cac8801500f2ca4f')
        eq_(Blake2SP(b'Hello').hexdigest(), '0d6bae0db99f99183d060f7994bb94b45c6490b2a0a628b8b1346ebea8ec1d66')

        eq_(xblake2sp(''), 'dd0e891776933f43c7d032b08a917e25741f8aa9a12c12e1cac8801500f2ca4f')
        eq_(xblake2sp('00'), 'a6b9eecc25227ad788c99d3f236debc8da408849e9a5178978727a81457f7239')

        long1 = '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f3031'
        eq_(xblake2sp(long1), '270affa6426f1a515c9b76dfc27d181fc2fd57d082a3ba2c1eef071533a6dfb7')

        long2 = long1 * 20
        eq_(xblake2sp(long2), '24a78d92592d0761a3681f32935225ca55ffb8eb16b55ab9481c89c59a985ff3')
        eq_(xblake2sp_slow(long2), '24a78d92592d0761a3681f32935225ca55ffb8eb16b55ab9481c89c59a985ff3')

def test_hmac_sha256():
    eq_(tohex(rarfile.hmac_sha256(b'key', b'data')), '5031fe3d989c6d1537a013fa6e739da23463fdaec3b70137d828e36ace221bd0')

def test_rar3_s2k():
    exp = ('a160cb31cb262e9231c0b6fc984fbb0d', 'aa54a659fb0c359b30f353a6343fb11d')
    key, iv = rarfile.rar3_s2k(b'password', unhexlify('00FF00'))
    eq_((tohex(key), tohex(iv)), exp)
    key, iv = rarfile.rar3_s2k(u'password', unhexlify('00FF00'))
    eq_((tohex(key), tohex(iv)), exp)

if rarfile._have_crypto:
    def test_pbkdf2_hmac_sha256():
        eq_(tohex(rarfile.pbkdf2_sha256(b'password', b'salt', 100)),
            '07e6997180cf7f12904f04100d405d34888fdf62af6d506a0ecc23b196fe99d8')

