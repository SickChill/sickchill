"""Read all test files.
"""

import io

from glob import glob

import rarfile

from nose.tools import *

_done_reading = set()

def run_reading_normal(fn, comment):
    try:
        rf = rarfile.RarFile(fn)
    except rarfile.NeedFirstVolume:
        return
    if rf.needs_password():
        rf.setpassword('password')
    eq_(rf.strerror(), None)
    eq_(rf.comment, comment)
    for ifn in rf.namelist():

        # full read
        rf.read(ifn)

        # read from stream
        item = rf.getinfo(ifn)
        f = rf.open(ifn)
        total = 0
        while 1:
            buf = f.read(1024)
            if not buf:
                break
            total += len(buf)
        f.close()
        eq_(total, item.file_size)

        # read from stream with readinto
        bbuf = bytearray(1024)
        with rf.open(ifn) as f:
            res = f.readinto(memoryview(bbuf))
            if res == 0:
                break

def run_reading_inmem(fn, comment):
    try:
        rf = rarfile.RarFile(fn)
    except rarfile.NeedFirstVolume:
        return
    if len(rf.volumelist()) > 1:
        return

    buf = io.open(fn, 'rb').read()
    run_reading_normal(io.BytesIO(buf), comment)

def run_reading(fn, comment=None):
    _done_reading.add(fn)
    run_reading_normal(fn, comment)
    run_reading_inmem(fn, comment)

def test_reading_rar3_ctime():
    run_reading('test/files/ctime0.rar')
    run_reading('test/files/ctime1.rar')
    run_reading('test/files/ctime2.rar')
    run_reading('test/files/ctime3.rar')
    run_reading('test/files/ctime4.rar')

def test_reading_rar2():
    run_reading('test/files/rar15-comment-lock.rar', u'RARcomment -----')
    run_reading('test/files/rar15-comment.rar', u'RARcomment -----')
    run_reading('test/files/rar202-comment-nopsw.rar', u'RARcomment')

def test_reading_rar3():
    run_reading('test/files/rar3-comment-plain.rar', u'RARcomment\n')
    run_reading('test/files/seektest.rar')
    run_reading('test/files/unicode.rar')
    run_reading('test/files/unicode2.rar')

def test_reading_rar2_psw():
    run_reading('test/files/rar202-comment-psw.rar', u'RARcomment')

def test_reading_rar3_psw():
    run_reading('test/files/rar3-comment-psw.rar', u'RARcomment\n')

if rarfile._have_crypto:
    def test_reading_rar3_hpsw():
        run_reading('test/files/rar3-comment-hpsw.rar', u'RARcomment\n')
else:
    @raises(rarfile.NoCrypto)
    def test_reading_rar3_hpsw_nocrypto():
        run_reading('test/files/rar3-comment-hpsw.rar', u'RARcomment\n')

def test_reading_rar3_vols():
    run_reading('test/files/rar3-old.rar')
    run_reading('test/files/rar3-vols.part1.rar')
    run_reading('test/files/rar3-vols.part2.rar')
    run_reading('test/files/rar3-vols.part3.rar')

def test_reading_rar5_blake():
    run_reading('test/files/rar5-blake.rar', u'RAR5 archive - blake\n')

def test_reading_rar5_crc():
    run_reading('test/files/rar5-crc.rar', u'RAR5 archive - crc\n')

def test_reading_rar5_links():
    run_reading('test/files/rar5-dups.rar')
    run_reading('test/files/rar5-hlink.rar')

def test_reading_rar5_quick_open():
    run_reading('test/files/rar5-quick-open.rar')

def test_reading_rar5_solid_qo():
    run_reading('test/files/rar5-solid-qo.rar')

def test_reading_rar5_solid():
    run_reading('test/files/rar5-solid.rar')

def test_reading_rar5_times():
    run_reading('test/files/rar5-times.rar')
    run_reading('test/files/rar5-times2.rar')

def test_reading_rar5_vols():
    run_reading('test/files/rar5-vols.part1.rar')
    run_reading('test/files/rar5-vols.part2.rar')
    run_reading('test/files/rar5-vols.part3.rar')

if rarfile._have_crypto:
    def test_reading_rar5_hpsw():
        run_reading('test/files/rar5-hpsw.rar', u'RAR5 archive - hdr-password\n')
else:
    @raises(rarfile.NoCrypto)
    def test_reading_rar5_hpsw():
        run_reading('test/files/rar5-hpsw.rar', u'RAR5 archive - hdr-password\n')

def test_reading_rar5_psw_blake():
    run_reading('test/files/rar5-psw-blake.rar', u'RAR5 archive - nohdr-password-blake\n')

def test_reading_rar5_psw():
    run_reading('test/files/rar5-psw.rar', u'RAR5 archive - nohdr-password\n')

def test_reading_missed():
    problems = []
    missed = []
    for fn in glob('test/files/*.rar'):
        if fn not in _done_reading:
            missed.append(fn)
    eq_(missed, problems)

