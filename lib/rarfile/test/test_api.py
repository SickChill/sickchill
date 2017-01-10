"""API tests.
"""

import sys
import io
import os

from nose.tools import *

import rarfile

#
# test start
#

@raises(NotImplementedError)
def test_bad_arc_mode_w():
    rarfile.RarFile('test/files/rar3-comment-plain.rar', 'w')

@raises(NotImplementedError)
def test_bad_arc_mode_rb():
    rarfile.RarFile('test/files/rar3-comment-plain.rar', 'rb')

@raises(ValueError)
def test_bad_errs():
    rarfile.RarFile('test/files/rar3-comment-plain.rar', 'r', errors='foo')

@raises(NotImplementedError)
def test_bad_open_mode_w():
    rf = rarfile.RarFile('test/files/rar3-comment-plain.rar')
    rf.open('qwe', 'w')

@raises(rarfile.PasswordRequired)
def test_bad_open_psw():
    rf = rarfile.RarFile('test/files/rar3-comment-psw.rar')
    rf.open('file1.txt')

@raises(ValueError)
def test_bad_filelike():
    rarfile.is_rarfile(bytearray(10))

def test_open_psw_late_rar3():
    rf = rarfile.RarFile('test/files/rar3-comment-psw.rar')
    rf.open('file1.txt', 'r', 'password').read()
    rf.open('file1.txt', 'r', u'password').read()

def test_open_psw_late_rar5():
    rf = rarfile.RarFile('test/files/rar5-psw.rar')
    rf.open('stest1.txt', 'r', 'password').read()
    rf.open('stest1.txt', 'r', u'password').read()

def test_read_psw_late_rar3():
    rf = rarfile.RarFile('test/files/rar3-comment-psw.rar')
    rf.read('file1.txt', 'password')
    rf.read('file1.txt', u'password')

def test_read_psw_late_rar5():
    rf = rarfile.RarFile('test/files/rar5-psw.rar')
    rf.read('stest1.txt', 'password')
    rf.read('stest1.txt', u'password')

@raises(rarfile.BadRarFile) # needs better error
def test_open_psw_late():
    rf = rarfile.RarFile('test/files/rar5-psw.rar')
    rf.read('stest1.txt', 'password222')

def test_detection():
    eq_(rarfile.is_rarfile('test/files/ctime4.rar.exp'), False)
    eq_(rarfile.is_rarfile('test/files/ctime4.rar'), True)
    eq_(rarfile.is_rarfile('test/files/rar5-crc.rar'), True)

@raises(rarfile.BadRarFile)
def test_signature_error():
    rarfile.RarFile('test/files/ctime4.rar.exp')

@raises(rarfile.BadRarFile)
def test_signature_error_mem():
    data = io.BytesIO(b'x'*40)
    rarfile.RarFile(data)

def test_with():
    with rarfile.RarFile('test/files/rar5-crc.rar') as rf:
        with rf.open('stest1.txt') as f:
            while 1:
                buf = f.read(7)
                if not buf:
                    break

def test_readline():
    def load_readline(rf, fn):
        with rf.open(fn) as f:
            tr = io.TextIOWrapper(io.BufferedReader(f))
            res = []
            while 1:
                ln = tr.readline()
                if not ln:
                    break
                res.append(ln)
        return res

    rf = rarfile.RarFile('test/files/seektest.rar')
    v1 = load_readline(rf, 'stest1.txt')
    v2 = load_readline(rf, 'stest2.txt')
    eq_(len(v1), 512)
    eq_(v1, v2)

_old_stdout = None
_buf_stdout = None

def install_buf():
    global _old_stdout, _buf_stdout
    _buf_stdout = io.StringIO()
    _old_stdout = sys.stdout
    sys.stdout = _buf_stdout

def uninstall_buf():
    sys.stdout = _old_stdout

@with_setup(install_buf, uninstall_buf)
def test_printdir():
    rf = rarfile.RarFile('test/files/seektest.rar')
    rf.printdir()
    eq_(_buf_stdout.getvalue(), u'stest1.txt\nstest2.txt\n')

def test_testrar():
    rf = rarfile.RarFile('test/files/seektest.rar')
    rf.testrar()

def test_testrar_mem():
    arc = open('test/files/seektest.rar', 'rb').read()
    rf = rarfile.RarFile(io.BytesIO(arc))
    rf.testrar()

def clean_extract_dirs():
    for dn in ['tmp/extract1', 'tmp/extract2', 'tmp/extract3']:
        for fn in ['stest1.txt', 'stest2.txt']:
            try:
                os.unlink(os.path.join(dn, fn))
            except OSError:
                pass
        try:
            os.rmdir(dn)
        except OSError:
            pass

@with_setup(clean_extract_dirs, clean_extract_dirs)
def test_extract():
    os.makedirs('tmp/extract1')
    os.makedirs('tmp/extract2')
    os.makedirs('tmp/extract3')
    rf = rarfile.RarFile('test/files/seektest.rar')

    rf.extractall('tmp/extract1')
    assert_true(os.path.isfile('tmp/extract1/stest1.txt'))
    assert_true(os.path.isfile('tmp/extract1/stest2.txt'))

    rf.extract('stest1.txt', 'tmp/extract2')
    assert_true(os.path.isfile('tmp/extract2/stest1.txt'))
    assert_false(os.path.isfile('tmp/extract2/stest2.txt'))

    inf = rf.getinfo('stest2.txt')
    rf.extract(inf, 'tmp/extract3')
    assert_false(os.path.isfile('tmp/extract3/stest1.txt'))
    assert_true(os.path.isfile('tmp/extract3/stest2.txt'))

    rf.extractall('tmp/extract2', ['stest1.txt'])
    assert_true(os.path.isfile('tmp/extract2/stest1.txt'))

    rf.extractall('tmp/extract3', [rf.getinfo('stest2.txt')])
    assert_true(os.path.isfile('tmp/extract3/stest2.txt'))

@with_setup(clean_extract_dirs, clean_extract_dirs)
def test_extract_mem():
    os.makedirs('tmp/extract1')
    os.makedirs('tmp/extract2')
    os.makedirs('tmp/extract3')
    arc = open('test/files/seektest.rar', 'rb').read()
    rf = rarfile.RarFile(io.BytesIO(arc))

    rf.extractall('tmp/extract1')
    assert_true(os.path.isfile('tmp/extract1/stest1.txt'))
    assert_true(os.path.isfile('tmp/extract1/stest2.txt'))

    rf.extract('stest1.txt', 'tmp/extract2')
    assert_true(os.path.isfile('tmp/extract2/stest1.txt'))
    assert_false(os.path.isfile('tmp/extract2/stest2.txt'))

    inf = rf.getinfo('stest2.txt')
    rf.extract(inf, 'tmp/extract3')
    assert_false(os.path.isfile('tmp/extract3/stest1.txt'))
    assert_true(os.path.isfile('tmp/extract3/stest2.txt'))

def test_infocb():
    infos = []
    def info_cb(info):
        infos.append( (info.type, info.needs_password(), info.isdir(), info._must_disable_hack()) )

    rf = rarfile.RarFile('test/files/seektest.rar', info_callback=info_cb)
    eq_(infos, [
        (rarfile.RAR_BLOCK_MAIN, False, False, False),
        (rarfile.RAR_BLOCK_FILE, False, False, False),
        (rarfile.RAR_BLOCK_FILE, False, False, False),
        (rarfile.RAR_BLOCK_ENDARC, False, False, False)])

    infos = []
    rf = rarfile.RarFile('test/files/rar5-solid-qo.rar', info_callback=info_cb)
    eq_(infos, [
        (rarfile.RAR_BLOCK_MAIN, False, False, True),
        (rarfile.RAR_BLOCK_FILE, False, False, False),
        (rarfile.RAR_BLOCK_FILE, False, False, True),
        (rarfile.RAR_BLOCK_FILE, False, False, True),
        (rarfile.RAR_BLOCK_FILE, False, False, True),
        (rarfile.RAR_BLOCK_SUB, False, False, False),
        (rarfile.RAR_BLOCK_ENDARC, False, False, False)])

def install_alt_tool():
    rarfile.ORIG_UNRAR_TOOL = 'x_unrar_missing'
    rarfile._check_unrar_tool()

def uninstall_alt_tool():
    rarfile.ORIG_UNRAR_TOOL = 'unrar'
    rarfile._check_unrar_tool()

def test_read_rar3():
    with rarfile.RarFile('test/files/seektest.rar') as rf:
        for fn in rf.namelist():
            rf.read(fn)

@with_setup(install_alt_tool, uninstall_alt_tool)
def test_alt_tool():
    #test_read_rar3()
    pass

