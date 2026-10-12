"""Extract .NET #US (user string) heap entries from a managed assembly."""
import struct
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clrmeta import Module  # noqa: E402


def user_strings(path):
    m = Module(path)
    off, size = m.streams['#US']
    d = m.data
    out = []
    i = 1
    end = off + size
    while i < size:
        p = off + i
        if p >= end:
            break
        # compressed uint length
        b0 = d[p]
        if b0 & 0x80 == 0:
            ln = b0
            hl = 1
        elif b0 & 0xC0 == 0x80:
            ln = ((b0 & 0x3F) << 8) | d[p + 1]
            hl = 2
        else:
            ln = ((b0 & 0x1F) << 24) | (d[p + 1] << 16) | (d[p + 2] << 8) | d[p + 3]
            hl = 4
        raw = d[p + hl:p + hl + ln]
        if len(raw) != ln:
            break
        if ln:
            try:
                s = raw[:-1].decode('utf-16le')
            except Exception:
                s = ''
            if s:
                out.append(s)
        i += hl + ln
    return out


if __name__ == '__main__':
    path = sys.argv[1]
    pat = sys.argv[2] if len(sys.argv) > 2 else None
    ss = user_strings(path)
    print('# %s : %d user strings' % (os.path.basename(path), len(ss)))
    if pat:
        for s in ss:
            if re.search(pat, s):
                print(repr(s))
    else:
        for s in ss:
            print(s)
