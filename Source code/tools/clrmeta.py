"""Minimal .NET (CLR) metadata reader + tiny IL inspector.

Pure-python, no dependencies. Supports PE32/PE32+ managed assemblies with a
compressed (#~) metadata table stream.

Features
  * TypeDef / MethodDef / Field discovery
  * TypeRef + MemberRef resolution (for call targets)
  * #US user string heap extraction
  * raw IL dump of a method with ldstr / call / field token resolution
"""
import struct
import sys
import os
import re


class Reader:
    def __init__(self, data):
        self.d = data

    def u16(self, o):
        return struct.unpack_from('<H', self.d, o)[0]

    def u32(self, o):
        return struct.unpack_from('<I', self.d, o)[0]


class Module:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        self._parse()

    # ---- PE / metadata ---------------------------------------------------
    def _rva_to_off(self, rva):
        for va, vsize, praw, rsize in self.sections:
            if va <= rva < va + max(vsize, rsize):
                return praw + (rva - va)
        raise ValueError('bad rva 0x%x' % rva)

    def _parse(self):
        d = self.data
        if d[:2] != b'MZ':
            raise ValueError('not PE')
        pe = struct.unpack_from('<I', d, 0x3c)[0]
        if d[pe:pe + 4] != b'PE\0\0':
            raise ValueError('no PE sig')
        coff = pe + 4
        nsec = struct.unpack_from('<H', d, coff + 2)[0]
        opt_size = struct.unpack_from('<H', d, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from('<H', d, opt)[0]
        ddir = opt + (96 if magic == 0x10b else 112)
        cli_rva = struct.unpack_from('<I', d, ddir + 14 * 8)[0]
        sec_off = opt + opt_size
        self.sections = []
        for i in range(nsec):
            o = sec_off + i * 40
            vsize, va, rsize, praw = struct.unpack_from('<IIII', d, o + 8)
            self.sections.append((va, vsize, praw, rsize))
        c = self._rva_to_off(cli_rva)
        md_rva, md_size = struct.unpack_from('<II', d, c + 8)
        m = self._rva_to_off(md_rva)
        assert d[m:m + 4] == b'BSJB', 'bad metadata signature'
        ver_len = struct.unpack_from('<I', d, m + 12)[0]
        p = m + 16 + ((ver_len + 3) & ~3)
        nstreams = struct.unpack_from('<H', d, p + 2)[0]
        p += 4
        streams = {}
        for _ in range(nstreams):
            soff, ssize = struct.unpack_from('<II', d, p)
            p += 8
            end = d.index(b'\0', p)
            sname = d[p:end].decode('ascii')
            p += (end - p) + 1
            p = (p + 3) & ~3
            streams[sname] = (m + soff, ssize)
        self.streams = streams
        self.str_off, self.str_size = streams['#Strings']
        tbl_off, tbl_size = streams.get('#~') or streams.get('#-')
        self._parse_tables(tbl_off, tbl_size)

    def _str(self, idx):
        if not idx:
            return ''
        end = self.data.index(b'\0', self.str_off + idx)
        return self.data[self.str_off + idx:end].decode('utf-8', 'replace')

    def _parse_tables(self, off, size):
        d = self.data
        heap = d[off + 6]
        valid = struct.unpack_from('<Q', d, off + 8)[0]
        p = off + 24
        rows = [0] * 64
        for i in range(64):
            if valid >> i & 1:
                rows[i] = struct.unpack_from('<I', d, p)[0]
                p += 4
        self.rows = rows
        self._heap = heap
        str_idx = 4 if heap & 1 else 2
        guid_idx = 4 if heap & 2 else 2
        blob_idx = 4 if heap & 4 else 2

        def simple(t):
            return 4 if rows[t] >= 65536 else 2

        def coded(bits, tables):
            mx = max([rows[t] for t in tables] + [0])
            return 4 if mx >= (1 << (16 - bits)) else 2

        def rd(o, w):
            return struct.unpack_from('<I' if w == 4 else '<H', d, o)[0]

        ri = {
            'str': str_idx, 'guid': guid_idx, 'blob': blob_idx,
            'TypeDef': simple(0x02), 'Field': simple(0x04), 'MethodDef': simple(0x06),
            'Param': simple(0x08), 'ModuleRef': simple(0x1A),
            'AssemblyRef': simple(0x23), 'TypeSpec': simple(0x1B),
        }
        coded_rs = coded(2, [0x00, 0x1A, 0x23, 0x01])
        coded_tdr = coded(2, [0x02, 0x01, 0x1B])
        coded_mrp = coded(3, [0x02, 0x01, 0x1A, 0x06, 0x1B])
        self._coded_rs, self._coded_tdr = coded_rs, coded_tdr

        rsize = {}
        rsize[0x00] = 2 + str_idx + 3 * guid_idx
        rsize[0x01] = coded_rs + 2 * str_idx
        rsize[0x02] = 4 + 2 * str_idx + coded_tdr + simple(0x04) + simple(0x06)
        rsize[0x04] = 2 + str_idx + blob_idx
        rsize[0x06] = 4 + 2 + 2 + str_idx + blob_idx + simple(0x08)
        rsize[0x08] = 2 + 2 + str_idx
        rsize[0x09] = simple(0x02) + coded_tdr
        rsize[0x0A] = coded_mrp + str_idx + blob_idx

        self.table_off = {}
        cur = p
        for t in range(0x0B):
            if not (valid >> t & 1):
                continue
            if t not in rsize:
                raise NotImplementedError('row size unknown for table 0x%02x' % t)
            self.table_off[t] = cur
            cur += rsize[t] * rows[t]

        # ---- Module ----
        self.module_name = ''
        if 0x00 in self.table_off:
            o = self.table_off[0x00] + 2
            self.module_name = self._str(rd(o, str_idx))

        # ---- TypeRef ----
        self.typerefs = []
        if 0x01 in self.table_off:
            to, sz = self.table_off[0x01], rsize[0x01]
            for i in range(rows[0x01]):
                o = to + i * sz + coded_rs
                nm = self._str(rd(o, str_idx))
                ns = self._str(rd(o + str_idx, str_idx))
                self.typerefs.append('%s.%s' % (ns, nm) if ns else nm)

        # ---- TypeDef ----
        self.typedefs = []
        if 0x02 in self.table_off:
            to, sz = self.table_off[0x02], rsize[0x02]
            for i in range(rows[0x02]):
                o = to + i * sz + 4
                nm = self._str(rd(o, str_idx))
                ns = self._str(rd(o + str_idx, str_idx))
                q = o + 2 * str_idx + coded_tdr
                fidx = rd(q, simple(0x04))
                midx = rd(q + simple(0x04), simple(0x06))
                self.typedefs.append({'ns': ns, 'name': nm, 'field': fidx, 'method': midx})

        # ---- MethodDef ----
        self.methods = []
        if 0x06 in self.table_off:
            to, sz = self.table_off[0x06], rsize[0x06]
            for i in range(rows[0x06]):
                o = to + i * sz
                rva = struct.unpack_from('<I', d, o)[0]
                nm = self._str(rd(o + 8, str_idx))
                self.methods.append({'name': nm, 'rva': rva})

        # ---- MemberRef ----
        self.memberrefs = []
        if 0x0A in self.table_off:
            to, sz = self.table_off[0x0A], rsize[0x0A]
            for i in range(rows[0x0A]):
                o = to + i * sz
                cls = rd(o, coded_mrp)
                nm = self._str(rd(o + coded_mrp, str_idx))
                tag = cls & 3 if coded_mrp == 2 else cls & 7
                idx = cls >> (2 if coded_mrp == 2 else 3)
                parent = '?'
                if tag == 0 and 0 < idx <= len(self.typedefs):
                    td = self.typedefs[idx - 1]
                    parent = '%s.%s' % (td['ns'], td['name']) if td['ns'] else td['name']
                elif tag == 1 and 0 < idx <= len(self.typerefs):
                    parent = self.typerefs[idx - 1]
                self.memberrefs.append({'name': nm, 'parent': parent})

    # ---- conveniences ----------------------------------------------------
    def types_with_methods(self):
        md_count = self.rows[0x06]
        tds = self.typedefs
        for i, td in enumerate(tds):
            start = td['method'] - 1
            end = (tds[i + 1]['method'] - 1) if i + 1 < len(tds) else md_count
            if end < start:
                end = start
            yield ('%s.%s' % (td['ns'], td['name']) if td['ns'] else td['name'],
                   [m['name'] for m in self.methods[start:end]])

    def method_info(self, full_type, method_name):
        md_count = self.rows[0x06]
        for i, td in enumerate(self.typedefs):
            nm = '%s.%s' % (td['ns'], td['name']) if td['ns'] else td['name']
            if nm != full_type:
                continue
            start = td['method'] - 1
            end = (self.typedefs[i + 1]['method'] - 1) if i + 1 < len(self.typedefs) else md_count
            for j in range(start, min(end, md_count)):
                if self.methods[j]['name'] == method_name:
                    return j, self.methods[j]
        return None, None

    # ---- #US -------------------------------------------------------------
    def user_string_at(self, us_offset):
        off, size = self.streams['#US']
        if us_offset >= size:
            return None
        p = off + us_offset
        b0 = self.data[p]
        if b0 & 0x80 == 0:
            ln, hl = b0, 1
        elif b0 & 0xC0 == 0x80:
            ln, hl = ((b0 & 0x3F) << 8) | self.data[p + 1], 2
        else:
            ln = ((b0 & 0x1F) << 24) | (self.data[p + 1] << 16) | (self.data[p + 2] << 8) | self.data[p + 3]
            hl = 4
        raw = self.data[p + hl:p + hl + ln]
        if len(raw) != ln or not ln:
            return None
        return raw[:-1].decode('utf-16le', 'replace')

    def user_strings(self):
        off, size = self.streams['#US']
        out = []
        i = 1
        while i < size:
            s = self.user_string_at(i)
            b0 = self.data[off + i]
            if b0 & 0x80 == 0:
                ln, hl = b0, 1
            elif b0 & 0xC0 == 0x80:
                ln, hl = ((b0 & 0x3F) << 8) | self.data[off + i + 1], 2
            else:
                ln = ((b0 & 0x1F) << 24) | (self.data[off + i + 1] << 16) | \
                      (self.data[off + i + 2] << 8) | self.data[off + i + 3]
                hl = 4
            if s:
                out.append(s)
            i += hl + ln
        return out

    # ---- IL --------------------------------------------------------------
    def il_bytes(self, rva):
        o = self._rva_to_off(rva)
        b = self.data[o]
        if b & 3 == 2:                      # tiny header
            return self.data[o + 1:o + 1 + (b >> 2)]
        code_size = struct.unpack_from('<I', self.data, o + 4)[0]
        return self.data[o + 12:o + 12 + code_size]

    def token_name(self, tok):
        table = tok >> 24
        idx = tok & 0xFFFFFF
        if table == 0x70:
            return '"%s"' % (self.user_string_at(idx) or '')
        if table == 0x06 and idx <= len(self.methods):
            return 'method:' + self.methods[idx - 1]['name']
        if table == 0x0A and idx <= len(self.memberrefs):
            mr = self.memberrefs[idx - 1]
            return '%s::%s' % (mr['parent'], mr['name'])
        if table == 0x01 and idx <= len(self.typerefs):
            return 'type:' + self.typerefs[idx - 1]
        if table == 0x02 and idx <= len(self.typedefs):
            td = self.typedefs[idx - 1]
            return 'type:%s.%s' % (td['ns'], td['name'])
        return '0x%08X' % tok

    def dump_il(self, full_type, method_name):
        i, info = self.method_info(full_type, method_name)
        if info is None:
            print('!! not found: %s::%s' % (full_type, method_name))
            return
        code = self.il_bytes(info['rva'])
        print('== IL %s::%s  (%d bytes)' % (full_type, method_name, len(code)))
        ops = {0x72: ('ldstr', 4), 0x28: ('call', 4), 0x6F: ('callvirt', 4),
               0x73: ('newobj', 4), 0x7B: ('ldfld', 4), 0x7D: ('stfld', 4),
               0x7E: ('ldsfld', 4), 0x80: ('stsfld', 4), 0xD0: ('ldtoken', 4),
               0x8C: ('box', 4), 0xA5: ('unbox.any', 4), 0x74: ('castclass', 4),
               0x75: ('isinst', 4), 0xFE06: ('ldftn', 4), 0xFE07: ('ldvirtftn', 4)}
        names = {0x00: 'nop', 0x02: 'ldarg.0', 0x03: 'ldarg.1', 0x04: 'ldarg.2',
                 0x05: 'ldarg.3', 0x06: 'ldloc.0', 0x07: 'ldloc.1', 0x08: 'ldloc.2',
                 0x09: 'ldloc.3', 0x0A: 'stloc.0', 0x0B: 'stloc.1', 0x0C: 'stloc.2',
                 0x0D: 'stloc.3', 0x14: 'ldnull', 0x15: 'ldc.i4.m1', 0x16: 'ldc.i4.0',
                 0x17: 'ldc.i4.1', 0x18: 'ldc.i4.2', 0x19: 'ldc.i4.3', 0x1A: 'ldc.i4.4',
                 0x1B: 'ldc.i4.5', 0x1C: 'ldc.i4.6', 0x1D: 'ldc.i4.7', 0x1E: 'ldc.i4.8',
                 0x25: 'dup', 0x26: 'pop', 0x2A: 'ret', 0x2B: 'br.s', 0x2C: 'brfalse.s',
                 0x2D: 'brtrue.s', 0x2E: 'beq.s', 0x39: 'brfalse', 0x3A: 'brtrue',
                 0x3B: 'beq', 0x58: 'add', 0x59: 'sub', 0x6E: 'conv.i4', 0x6A: 'conv.i8',
                 0x6C: 'conv.r4', 0x6D: 'conv.r8', 0x16: 'ldc.i4.0'}
        pc = 0
        out = []
        while pc < len(code):
            op = code[pc]
            start = pc
            if op == 0xFE:
                op2 = code[pc + 1]
                key = 0xFE00 | op2
                nm, sz = ops.get(key, ('fe.%02x' % op2, 0))
                pc += 2
            else:
                nm, sz = ops.get(op, (names.get(op), 0))
                if nm is None:
                    nm, sz = 'op_%02x' % op, 0
                pc += 1
            arg = ''
            if sz == 4:
                tok = struct.unpack_from('<I', code, pc)[0]
                pc += 4
                arg = ' 0x%08X %s' % (tok, self.token_name(tok))
            elif nm in ('br.s', 'brfalse.s', 'brtrue.s', 'beq.s'):
                arg = ' +%d' % struct.unpack_from('<b', code, pc)[0]
                pc += 1
            out.append('%04X  %-12s%s' % (start, nm, arg))
        print('\n'.join(out))


def main():
    path = sys.argv[1]
    m = Module(path)
    if len(sys.argv) > 2 and sys.argv[2] == '--il':
        m.dump_il(sys.argv[3], sys.argv[4])
        return
    pat = sys.argv[2] if len(sys.argv) > 2 else None
    print('# %s  typedefs=%d methods=%d userstrings=%d' %
          (os.path.basename(path), m.rows[0x02], m.rows[0x06], len(m.user_strings())))
    for name, methods in m.types_with_methods():
        if pat and not re.search(pat, name, re.I):
            continue
        print('==', name)
        for x in methods:
            print('     ', x)


if __name__ == '__main__':
    main()
