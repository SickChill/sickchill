#! /usr/bin/env python

"""Dump archive contents, test extraction."""

import sys
import rarfile as rf
from binascii import crc32, hexlify
from datetime import datetime

try:
    bytearray
except NameError:
    import array
    def bytearray(v):
        return array.array('B', v)

rf.UNICODE_COMMENTS = 1
rf.USE_DATETIME = 1

usage = """
dumprar [switches] [ARC1 ARC2 ...] [@ARCLIST]
switches:
  @file      read archive names from file
  -pPSW      set password
  -Ccharset  set fallback charset
  -v         increase verbosity
  -t         attemt to read all files
  -x         write read files out
  -c         show archive comment
  -h         show usage
  --         stop switch parsing
""".strip()

os_list = ['DOS', 'OS2', 'WIN', 'UNIX', 'MACOS', 'BEOS']

block_strs = ['MARK', 'MAIN', 'FILE', 'OLD_COMMENT', 'OLD_EXTRA',
              'OLD_SUB', 'OLD_RECOVERY', 'OLD_AUTH', 'SUB', 'ENDARC']

def rarType(type):
    if type < rf.RAR_BLOCK_MARK or type > rf.RAR_BLOCK_ENDARC:
        return "*UNKNOWN*"
    return block_strs[type - rf.RAR_BLOCK_MARK]
                                 
main_bits = (
    (rf.RAR_MAIN_VOLUME, "VOL"),
    (rf.RAR_MAIN_COMMENT, "COMMENT"),
    (rf.RAR_MAIN_LOCK, "LOCK"),
    (rf.RAR_MAIN_SOLID, "SOLID"),
    (rf.RAR_MAIN_NEWNUMBERING, "NEWNR"),
    (rf.RAR_MAIN_AUTH, "AUTH"),
    (rf.RAR_MAIN_RECOVERY, "RECOVERY"),
    (rf.RAR_MAIN_PASSWORD, "PASSWORD"),
    (rf.RAR_MAIN_FIRSTVOLUME, "FIRSTVOL"),
    (rf.RAR_SKIP_IF_UNKNOWN, "SKIP"),
    (rf.RAR_LONG_BLOCK, "LONG"),
)

endarc_bits = (
    (rf.RAR_ENDARC_NEXT_VOLUME, "NEXTVOL"),
    (rf.RAR_ENDARC_DATACRC, "DATACRC"),
    (rf.RAR_ENDARC_REVSPACE, "REVSPACE"),
    (rf.RAR_ENDARC_VOLNR, "VOLNR"),
    (rf.RAR_SKIP_IF_UNKNOWN, "SKIP"),
    (rf.RAR_LONG_BLOCK, "LONG"),
)

file_bits = (
    (rf.RAR_FILE_SPLIT_BEFORE, "SPLIT_BEFORE"),
    (rf.RAR_FILE_SPLIT_AFTER, "SPLIT_AFTER"),
    (rf.RAR_FILE_PASSWORD, "PASSWORD"),
    (rf.RAR_FILE_COMMENT, "COMMENT"),
    (rf.RAR_FILE_SOLID, "SOLID"),
    (rf.RAR_FILE_LARGE, "LARGE"),
    (rf.RAR_FILE_UNICODE, "UNICODE"),
    (rf.RAR_FILE_SALT, "SALT"),
    (rf.RAR_FILE_VERSION, "VERSION"),
    (rf.RAR_FILE_EXTTIME, "EXTTIME"),
    (rf.RAR_FILE_EXTFLAGS, "EXTFLAGS"),
    (rf.RAR_SKIP_IF_UNKNOWN, "SKIP"),
    (rf.RAR_LONG_BLOCK, "LONG"),
)

generic_bits = (
    (rf.RAR_SKIP_IF_UNKNOWN, "SKIP"),
    (rf.RAR_LONG_BLOCK, "LONG"),
)

file_parms = ("D64", "D128", "D256", "D512",
              "D1024", "D2048", "D4096", "DIR")

def xprint(m, *args):
    if sys.hexversion < 0x3000000:
        m = m.decode('utf8')
    if args:
        m = m % args
    if sys.hexversion < 0x3000000:
        m = m.encode('utf8')
    sys.stdout.write(m)
    sys.stdout.write('\n')

def render_flags(flags, bit_list):
    res = []
    known = 0
    for bit in bit_list:
        known = known | bit[0]
        if flags & bit[0]:
            res.append(bit[1])
    unknown = flags & ~known
    n = 0
    while unknown:
        if unknown & 1:
            res.append("UNK_%04x" % (1 << n))
        unknown = unknown >> 1
        n += 1

    return ",".join(res)

def get_file_flags(flags):
    res = render_flags(flags & ~rf.RAR_FILE_DICTMASK, file_bits)

    xf = (flags & rf.RAR_FILE_DICTMASK) >> 5
    res += "," + file_parms[xf]
    return res

def get_main_flags(flags):
    return render_flags(flags, main_bits)

def get_endarc_flags(flags):
    return render_flags(flags, endarc_bits)

def get_generic_flags(flags):
    return render_flags(flags, generic_bits)

def fmt_time(t):
    if isinstance(t, datetime):
        return t.isoformat(' ')
    return "%04d-%02d-%02d %02d:%02d:%02d" % t

def show_item(h):
    st = rarType(h.type)
    unknown = h.header_size - h.header_base
    xprint("%s: hdrlen=%d datlen=%d hdr_unknown=%d", st, h.header_size,
                h.add_size, unknown)
    if unknown > 0 and cf_verbose > 1:
        dat = h.header_data[h.header_base : ]
        xprint("  unknown: %s", hexlify(dat))
    if h.type in (rf.RAR_BLOCK_FILE, rf.RAR_BLOCK_SUB):
        if h.host_os == rf.RAR_OS_UNIX:
            s_mode = "0%o" % h.mode
        else:
            s_mode = "0x%x" % h.mode
        xprint("  flags=0x%04x:%s", h.flags, get_file_flags(h.flags))
        if h.host_os >= 0 and h.host_os < len(os_list):
            s_os = os_list[h.host_os]
        else:
            s_os = "?"
        xprint("  os=%d:%s ver=%d mode=%s meth=%c cmp=%d dec=%d vol=%d",
                h.host_os, s_os,
                h.extract_version, s_mode, h.compress_type,
                h.compress_size, h.file_size, h.volume)
        ucrc = (h.CRC + (1 << 32)) & ((1 << 32) - 1)
        xprint("  crc=0x%08x (%d) time=%s", ucrc, h.CRC, fmt_time(h.date_time))
        xprint("  name=%s", h.filename)
        if h.mtime:
            xprint("  mtime=%s", fmt_time(h.mtime))
        if h.ctime:
            xprint("  ctime=%s", fmt_time(h.ctime))
        if h.atime:
            xprint("  atime=%s", fmt_time(h.atime))
        if h.arctime:
            xprint("  arctime=%s", fmt_time(h.arctime))
    elif h.type == rf.RAR_BLOCK_MAIN:
        xprint("  flags=0x%04x:%s", h.flags, get_main_flags(h.flags))
    elif h.type == rf.RAR_BLOCK_ENDARC:
        xprint("  flags=0x%04x:%s", h.flags, get_endarc_flags(h.flags))
    elif h.type == rf.RAR_BLOCK_MARK:
        xprint("  flags=0x%04x:", h.flags)
    else:
        xprint("  flags=0x%04x:%s", h.flags, get_generic_flags(h.flags))

    if h.comment is not None:
        cm = repr(h.comment)
        if cm[0] == 'u':
            cm = cm[1:]
        xprint("  comment=%s", cm)

cf_show_comment = 0
cf_verbose = 0
cf_charset = None
cf_extract = 0
cf_test_read = 0
cf_test_unrar = 0

def check_crc(f, inf):
    ucrc = f.CRC
    if ucrc < 0:
        ucrc += (long(1) << 32)
    if ucrc != inf.CRC:
        print ('crc error')

def test_read_long(r, inf):
    f = r.open(inf.filename)
    total = 0
    while 1:
        data = f.read(8192)
        if not data:
            break
        total += len(data)
    if total != inf.file_size:
        xprint("\n *** %s has corrupt file: %s ***", r.rarfile, inf.filename)
        xprint(" *** short read: got=%d, need=%d ***\n", total, inf.file_size)
    check_crc(f, inf)

    # test .seek() & .readinto()
    if cf_test_read > 1:
        f.seek(0,0)

        # hack: re-enable crc calc
        f.crc_check = 1
        f.CRC = 0

        total = 0
        buf = bytearray(rf.ZERO*4096)
        while 1:
            res = f.readinto(buf)
            if not res:
                break
            total += res
        if inf.file_size != total:
            xprint(" *** readinto failed: got=%d, need=%d ***\n", total, inf.file_size)
        check_crc(f, inf)
    f.close()

def test_read(r, inf):
    test_read_long(r, inf)


def test_real(fn, psw):
    xprint("Archive: %s", fn)

    cb = None
    if cf_verbose > 1:
        cb = show_item

    # check if rar
    if not rf.is_rarfile(fn):
        xprint(" --- %s is not a RAR file ---", fn)
        return

    # open
    r = rf.RarFile(fn, charset = cf_charset, info_callback = cb)
    # set password
    if r.needs_password():
        if psw:
            r.setpassword(psw)
        else:
            xprint(" --- %s requires password ---", fn)
            return

    # show comment
    if cf_show_comment and r.comment:
        for ln in r.comment.split('\n'):
            xprint("    %s", ln)
    elif cf_verbose == 1 and r.comment:
        cm = repr(r.comment)
        if cm[0] == 'u':
            cm = cm[1:]
        xprint("  comment=%s", cm)

    # process
    for n in r.namelist():
        inf = r.getinfo(n)
        if inf.isdir():
            continue
        if cf_verbose == 1:
            show_item(inf)
        if cf_test_read:
            test_read(r, inf)

    if cf_extract:
        r.extractall()
        for inf in r.infolist():
            r.extract(inf)

    if cf_test_unrar:
        r.testrar()

def test(fn, psw):
    try:
        test_real(fn, psw)
    except rf.NeedFirstVolume:
        xprint(" --- %s is middle part of multi-vol archive ---", fn)
    except rf.Error:
        exc, msg, tb = sys.exc_info()
        xprint("\n *** %s: %s ***\n", exc.__name__, msg)
        del tb
    except IOError:
        exc, msg, tb = sys.exc_info()
        xprint("\n *** %s: %s ***\n", exc.__name__, msg)
        del tb

def main():
    global cf_verbose, cf_show_comment, cf_charset
    global cf_extract, cf_test_read, cf_test_unrar

    # parse args
    args = []
    psw = None
    noswitch = False
    for a in sys.argv[1:]:
        if noswitch:
            args.append(a)
        elif a[0] == "@":
            for ln in open(a[1:], 'r'):
                fn = ln[:-1]
                args.append(fn)
        elif a[0] != '-':
            args.append(a)
        elif a[1] == 'p':
            psw = a[2:]
        elif a == '--':
            noswitch = True
        elif a == '-h':
            xprint(usage)
            return
        elif a == '-v':
            cf_verbose += 1
        elif a == '-c':
            cf_show_comment = 1
        elif a == '-x':
            cf_extract = 1
        elif a == '-t':
            cf_test_read += 1
        elif a == '-T':
            cf_test_unrar = 1
        elif a[1] == 'C':
            cf_charset = a[2:]
        else:
            raise Exception("unknown switch: "+a)
    if not args:
        xprint(usage)

    for fn in args:
        test(fn, psw)

    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

