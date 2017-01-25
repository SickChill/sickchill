"""Test seeking on files.
"""

import io
import rarfile

from nose.tools import *

ARC = 'test/files/seektest.rar'

def do_seek(f, pos, lim):
    ofs = pos*4
    fsize = lim*4

    if ofs < 0:
        exp = 0
    elif ofs > fsize:
        exp = fsize
    else:
        exp = ofs

    f.seek(ofs)

    got = f.tell()

    eq_(got, exp)
    ln = f.read(4)
    if got == fsize and ln:
        raise Exception('unexpected read')
    if not ln and got < fsize:
        raise Exception('unexpected read failure')
    if ln:
        spos = int(ln)
        eq_(spos*4, got)

def run_seek(rf, fn):
    inf = rf.getinfo(fn)
    cnt = int(inf.file_size / 4)
    f = rf.open(fn)

    do_seek(f, int(cnt/2), cnt)
    do_seek(f, 0, cnt)

    for i in range(int(cnt/2)):
        do_seek(f, i*2, cnt)

    for i in range(cnt):
        do_seek(f, i*2 - int(cnt / 2), cnt)

    for i in range(cnt + 10):
        do_seek(f, cnt - i - 5, cnt)

    f.close()

def run_arc(arc, desc):
    files = ['stest1.txt', 'stest2.txt']
    rf = rarfile.RarFile(arc)
    for fn in files:
        run_seek(rf, fn)

def test_seek_filename():
    run_arc(ARC, "fn")

def test_seek_stringio():
    data = open(ARC, 'rb').read()

    # filelike: cStringIO
    try:
        import cStringIO
        run_arc(cStringIO.StringIO(data), "cStringIO")
    except ImportError:
        pass

    # filelike: StringIO
    try:
        import StringIO
        run_arc(StringIO.StringIO(data), "StringIO")
    except ImportError:
        pass

def test_seek_bytesio():
    # filelike: io.BytesIO, io.open()
    data = open(ARC, 'rb').read()
    run_arc(io.BytesIO(data), "io.BytesIO")

def test_seek_open():
    # filelike: file()
    run_arc(open(ARC, 'rb'), "open")

def test_seek_ioopen():
    # filelike: io.open()
    run_arc(io.open(ARC, 'rb'), "io.open")

