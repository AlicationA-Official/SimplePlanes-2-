"""Build a translatable string inventory from Game.dll / Jundroo.Common.dll.

Heuristically classifies .NET user strings and records which methods reference
them (approximate, via validated ldstr token scan of IL bodies).
Outputs a UTF-8 CSV.
"""
import csv
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clrmeta import Module  # noqa: E402

MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sp2_strings_en.csv')

PLACEHOLDER = re.compile(r'\{\d+')
TMP_TAG = re.compile(r'</?(color|b|i|size|sprite|align|line-height|indent|mark|u|s|style|link|lowercase|uppercase|smallcaps|nobr|space|page|pos|mspace|font-weight|cspace|voffset)\b', re.I)

# words that strongly suggest a developer/diagnostic message rather than UI text
DEV_HINT = re.compile(
    r'\b(threw|exception|stack|null ref|assert|trace|log|debug|deserializ|serializ|'
    r'failed to parse|could not|couldn\'t|unable to|not found|invalid|mismatch|'
    r'expected|attempted|attempting|aborting|unsupported|malformed|duplicate|'
    r'leaked|registered|initialized|unregistered|deprecated)\b', re.I)


def is_ui_candidate(s):
    if len(s) < 2 or len(s) > 160:
        return False
    if '{' in s and not PLACEHOLDER.search(s):
        return False
    if not re.search(r'[A-Za-z]', s):
        return False
    if s.startswith('http') or s.startswith('Assets/') or s.startswith('Assets\\'):
        return False
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', s) and len(s) > 20:
        return False          # camelCase identifier
    if re.match(r'^[a-z]', s) and ' ' not in s:
        return False
    if DEV_HINT.search(s):
        return False
    return True


def classify(s):
    if PLACEHOLDER.search(s) or TMP_TAG.search(s):
        return 'ui_template'
    words = s.split()
    if len(words) == 1 and s[:1].isupper():
        return 'ui_label'
    if len(s) <= 24 and not s.endswith(('.', '!', '?')):
        return 'ui_short'
    return 'ui_text'


def build():
    rows = []
    for dll in ('Game.dll', 'Jundroo.Common.dll', 'Jundroo.Packages.dll'):
        path = os.path.join(MANAGED, dll)
        if not os.path.exists(path):
            continue
        m = Module(path)
        off, size = m.streams['#US']
        # valid #US entry offsets
        valid = set()
        i = 1
        while i < size:
            valid.add(i)
            b0 = m.data[off + i]
            if b0 & 0x80 == 0:
                ln, hl = b0, 1
            elif b0 & 0xC0 == 0x80:
                ln, hl = ((b0 & 0x3F) << 8) | m.data[off + i + 1], 2
            else:
                ln = ((b0 & 0x1F) << 24) | (m.data[off + i + 1] << 16) | \
                     (m.data[off + i + 2] << 8) | m.data[off + i + 3]
                hl = 4
            i += hl + ln
        # map string -> referencing method names (validated ldstr scan)
        refs = {}
        tds = m.typedefs
        md_count = m.rows[0x06]
        owner = [''] * md_count
        for k, td in enumerate(tds):
            start = td['method'] - 1
            end = (tds[k + 1]['method'] - 1) if k + 1 < len(tds) else md_count
            nm = '%s.%s' % (td['ns'], td['name']) if td['ns'] else td['name']
            for j in range(start, min(end, md_count)):
                owner[j] = nm
        for j, mi in enumerate(m.methods):
            if not mi['rva']:
                continue
            try:
                code = m.il_bytes(mi['rva'])
            except Exception:
                continue
            for mo in re.finditer(b'\x72', code):
                p = mo.start() + 1
                if p + 4 > len(code):
                    break
                tok = struct.unpack_from('<I', code, p)[0]
                if tok >> 24 != 0x70:
                    continue
                us = tok & 0xFFFFFF
                if us not in valid:
                    continue
                s = m.user_string_at(us)
                if s is None:
                    continue
                refs.setdefault(s, set()).add(owner[j])
        seen = set()
        for s in m.user_strings():
            if s in seen:
                continue
            seen.add(s)
            if not is_ui_candidate(s):
                continue
            rows.append({
                'source_en': s,
                'kind': classify(s),
                'placeholders': ' '.join(sorted(set(PLACEHOLDER.findall(s)))),
                'tmp_tags': ' '.join(sorted(set(x.lower() for x in TMP_TAG.findall(s)))),
                'length': len(s),
                'assembly': dll,
                'referenced_by': '; '.join(sorted(refs.get(s, ()))[:4]),
            })
    rows.sort(key=lambda r: (r['kind'], r['source_en']))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_en', 'kind', 'placeholders', 'tmp_tags',
                                          'length', 'assembly', 'referenced_by'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('wrote %d rows -> %s' % (len(rows), OUT))
    from collections import Counter
    print(Counter(r['kind'] for r in rows))


if __name__ == '__main__':
    build()
