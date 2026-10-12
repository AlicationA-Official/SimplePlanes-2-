"""Scan a Unity data file for embedded TTF/OTF font blobs and report family names."""
import struct
import sys
import os


def read_name_table(d, base):
    try:
        ver, num_tables = struct.unpack_from('>IH', d, base)
    except struct.error:
        return None
    if num_tables == 0 or num_tables > 100:
        return None
    name_off = name_len = None
    for i in range(num_tables):
        p = base + 12 + i * 16
        try:
            tag, chks, off, ln = struct.unpack_from('>4sIII', d, p)
        except struct.error:
            return None
        if tag == b'name':
            name_off, name_len = base + off, ln
    if name_off is None or name_off + 6 > len(d):
        return None
    try:
        fmt, count, str_off = struct.unpack_from('>HHH', d, name_off)
    except struct.error:
        return None
    names = {}
    for i in range(count):
        p = name_off + 6 + i * 12
        if p + 12 > len(d):
            break
        pid, eid, lid, nid, ln, off = struct.unpack_from('>HHHHHH', d, p)
        if nid not in (1, 2, 4, 6):
            continue
        raw = d[name_off + str_off + off: name_off + str_off + off + ln]
        try:
            s = raw.decode('utf-16-be') if (pid == 3 or pid == 0) else raw.decode('latin1')
        except Exception:
            continue
        names.setdefault(nid, s)
    if not names:
        return None
    return names


def scan(path, limit=200):
    d = open(path, 'rb').read()
    found = []
    for sig in (b'\x00\x01\x00\x00', b'OTTO', b'true', b'ttcf'):
        start = 0
        while True:
            i = d.find(sig, start)
            if i < 0:
                break
            start = i + 1
            if sig == b'ttcf':
                continue
            nm = read_name_table(d, i)
            if nm and (1 in nm or 4 in nm):
                found.append((i, sig, nm))
                if len(found) >= limit:
                    break
        if len(found) >= limit:
            break
    return found, len(d)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        found, size = scan(p)
        print('==== %s (%d bytes) : %d font blobs' % (os.path.basename(p), size, len(found)))
        for off, sig, nm in found:
            print('   0x%09X %-6s family=%-40s full=%s' %
                  (off, sig.decode('latin1', 'replace'), nm.get(1, '?'), nm.get(4, '')))
