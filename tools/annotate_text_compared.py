"""给"被用作文本比较"的字符串标注所属方法，并打印该处上下文。"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clrmeta import Module  # noqa: E402
from find_text_compared import us_pairs, gettext_tokens  # noqa: E402

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')


def main():
    m = Module(os.path.join(MANAGED, 'Game.dll'))
    blob = m.data
    get_text = gettext_tokens(m)

    # method index -> (owner type, name, file offset, length)
    md_count = m.rows[0x06]
    owner = [''] * md_count
    tds = m.typedefs
    for k, td in enumerate(tds):
        start = td['method'] - 1
        end = (tds[k + 1]['method'] - 1) if k + 1 < len(tds) else md_count
        nm = '%s.%s' % (td['ns'], td['name']) if td['ns'] else td['name']
        for j in range(start, min(end, md_count)):
            owner[j] = nm
    ranges = []
    for i, meth in enumerate(m.methods):
        if not meth['rva']:
            continue
        try:
            off = m._rva_to_off(meth['rva'])
            code = m.il_bytes(meth['rva'])
        except Exception:
            continue
        ranges.append((off, len(code), owner[i], meth['name']))
    ranges.sort()

    def owner_of(pos):
        lo, hi = 0, len(ranges) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            off, ln, typ, name = ranges[mid]
            if off <= pos < off + ln:
                return typ, name
            if pos < off:
                hi = mid - 1
            else:
                lo = mid + 1
        return best or ('?', '?')

    j = json.load(open(DICT, encoding='utf-8-sig'))
    translated = dict(j['entries'])
    for e in j['contextEntries']:
        translated.setdefault(e['key'], e['value'])

    for offset, s in us_pairs(m):
        if s not in translated:
            continue
        token = 0x70000000 | offset
        needle = b'\x72' + struct.pack('<I', token)
        pos = blob.find(needle)
        while pos >= 0:
            window = blob[max(0, pos - 48):pos]
            matched = any((op + struct.pack('<I', gt)) in window
                          for gt in get_text for op in (b'\x6f', b'\x28'))
            if matched:
                typ, name = owner_of(pos)
                print('%-34r -> %-14r  @ %s::%s' % (s, translated[s], typ, name))
            pos = blob.find(needle, pos + 1)


if __name__ == '__main__':
    main()
