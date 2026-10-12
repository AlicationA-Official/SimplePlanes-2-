"""从 resources.assets 的 Rewired 数据里解析动作显示名（Unity 长度前缀字符串格式）。

按键绑定提示是运行时拼出来的：
    "Press a key to assign it to\n" + "<color=#ffff00>" + 动作名 + "</color>"
    + "\n\nModifier keys may also be used. To assign a modifier key alone, hold it down for 1 second."
所以要整段汉化，必须知道全部动作名。
"""
import json
import os
import re
import struct
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')


def parse_strings(blob, start, end):
    """按 [u32 长度][UTF-8 字节][补齐到 4 字节] 解析。"""
    out = []
    i = start
    while i < end - 8:
        ln = struct.unpack_from('<I', blob, i)[0]
        if 1 <= ln <= 60:
            raw = blob[i + 4:i + 4 + ln]
            if all(0x20 <= c <= 0x7e for c in raw):
                pad = (4 - (ln % 4)) % 4
                if all(c == 0 for c in blob[i + 4 + ln:i + 4 + ln + pad]):
                    out.append((i, raw.decode('ascii')))
                    i += 4 + ln + pad
                    continue
        i += 1
    return out


def main():
    blob = open(ASSETS, 'rb').read()
    anchor = blob.find(b'Activate 1')
    print('anchor 0x%X' % anchor)
    pairs = parse_strings(blob, anchor - 200, anchor + 400000)
    print('解析出字符串条目: %d' % len(pairs))

    internal, display = [], []
    for off, s in pairs:
        if ' ' in s or not re.search(r'[A-Z]', s[1:]):
            display.append(s)
        else:
            internal.append(s)

    # 过滤明显不是动作名的（路径、扩展名、代码标识）
    display = [s for s in display
               if not re.search(r'(\.|/|_|^[a-z]|^[A-Z]{2,}$)', s)]

    print('显示名候选: %d' % len(display))
    print('内部名: %d' % len(internal))
    print()
    print('前 40 个显示名:')
    for s in display[:40]:
        print('   ', s)

    j = json.load(open(DICT, encoding='utf-8-sig'))
    tr = dict(j['entries'])
    for e in j['contextEntries']:
        tr.setdefault(e['key'], e['value'])

    untranslated = [s for s in display if s not in tr]
    print()
    print('其中未翻译的: %d' % len(untranslated))
    for s in untranslated[:30]:
        print('   ', s)

    out = os.path.join(WS, 'data', 'action_names.json')
    json.dump({'display': display, 'translated': {s: tr[s] for s in display if s in tr}},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print()
    print('written %s' % out)


if __name__ == '__main__':
    main()
