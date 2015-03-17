import os
import platform
import stat
try:
    from shutil import SpecialFileError, Error
except:
    from shutil import Error
from shutil import _samefile


def copyfile_custom(src, dst):
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error("`%s` and `%s` are the same file" % (src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                try:
                    raise SpecialFileError("`%s` is a named pipe" % fn)
                except NameError:
                    raise Error("`%s` is a named pipe" % fn)

    try:
        # Windows
        O_BINARY = os.O_BINARY
    except:
        O_BINARY = 0

    READ_FLAGS = os.O_RDONLY | O_BINARY
    WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
    BUFFER_SIZE = 128*1024

    try:
        fin = os.open(src, READ_FLAGS)
        fout = os.open(dst, WRITE_FLAGS)
        for x in iter(lambda: os.read(fin, BUFFER_SIZE), ""):
            os.write(fout, x)
    except Exception as e:
        raise
    finally:
        try:
            os.close(fin)
            os.close(fout)
        except:
            pass
