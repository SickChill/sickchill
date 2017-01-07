"""test corrupt file parsing.
"""

import rarfile
import glob
import io

def try_read(tmpfn):
    try:
        rf = rarfile.RarFile(tmpfn, errors='strict')
        if rf.needs_password():
            rf.setpassword('password')
    except rarfile.Error:
        return
    for fn in rf.namelist():
        try:
            data = rf.read(fn)
        except rarfile.Error:
            pass

def process_rar(rarfn, quick=False):
    data = open(rarfn, "rb").read()
    for n in range(len(data)):
        bad = data[:n]
        try_read(io.BytesIO(bad))

    crap = b'\x00\xff\x01\x80\x7f'
    if quick:
        crap = b'\xff'
    for n in range(1, len(data)):
        for i in range(len(crap)):
            c = crap[i:i+1]
            bad = data[:n - 1] + c + data[n:]
            try_read(io.BytesIO(bad))

def test_corrupt_quick_rar3():
    process_rar("test/files/rar3-comment-plain.rar", True)

def test_corrupt_quick_rar5():
    process_rar("test/files/rar5-times.rar", True)

def test_corrupt_all():
    test_rar_list = glob.glob('test/files/*.rar')
    test_rar_list = []
    for rar in test_rar_list:
        process_rar(rar)

if __name__ == '__main__':
    test_corrupt_quick_rar5()

