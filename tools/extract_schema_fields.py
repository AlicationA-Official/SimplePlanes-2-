"""提取 Game.dll 中"零件属性表"里的三段文案：Label / Header / Tooltip。

这些文案不在 #US 托管字符串堆里，而是序列化在 DLL 的元数据块中，格式为：

    0e <名称长度> <名称> <文本长度> <文本>

例如：
    0e 05 'Label'   0d 'Particle Size'  54 08 05 'Order' ...
    0e 06 'Header'  0c 'Plume Tuning'   54 02 ...
    0e 07 'Tooltip' 19 'How big each particle is'

用法：
    python extract_schema_fields.py             # 只统计未翻译数量
    python extract_schema_fields.py --missing   # 输出未翻译清单
"""
import argparse
import json
import os
import re
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLL = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed\Game.dll'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')
TAGS = ['Label', 'Header', 'Tooltip']


def grab(blob, tag):
    out, seen = [], []
    pat = re.compile(b'\x0e' + bytes([len(tag)]) + tag.encode() + b'(.)', re.S)
    for m in pat.finditer(blob):
        ln = m.group(1)[0]
        s = blob[m.end():m.end() + ln]
        if ln >= 2 and all(32 <= c < 127 for c in s):
            out.append(s.decode('ascii'))
    for x in out:
        if x not in seen:
            seen.append(x)
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--missing', action='store_true')
    args = ap.parse_args()

    blob = open(DLL, 'rb').read()
    j = json.load(open(DICT, encoding='utf-8-sig'))
    tr = set(j['entries']) | {e['key'] for e in j['contextEntries']}

    total_missing = 0
    for tag in TAGS:
        items = grab(blob, tag)
        miss = [s for s in items if s not in tr]
        total_missing += len(miss)
        print('%-8s 共 %3d 条，未翻译 %d 条' % (tag, len(items), len(miss)))
        if args.missing:
            for s in miss:
                print('    %s' % s)
    if total_missing == 0:
        print('=> 零件属性文案已 100% 覆盖')
    return 0


if __name__ == '__main__':
    sys.exit(main())
