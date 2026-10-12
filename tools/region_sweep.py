"""Extract UI strings from the Game.dll region that holds designer tips and the
craft-properties labels, and report which are missing."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed\Game.dll'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

blob = open(GAME, 'rb').read()
j = json.load(open(DICT, encoding='utf-8-sig'))
E = set(j['entries'])
C = {e['key'] for e in j['contextEntries']}

RUN = re.compile(rb'(?:[\x20-\x7e]\x00){4,}')
lo, hi = 0x551800, 0x552600
cands = []
for m in RUN.finditer(blob[lo:hi]):
    s = m.group().decode('utf-16-le').strip()
    if not s or len(s) > 160:
        continue
    if not re.match(r'^[A-Z]', s):
        continue
    if re.search(r'(^[a-z-]+$|/|\.xml|\.png|\{0\}|^[A-Za-z]+_[A-Za-z]+$)', s):
        continue
    cands.append(s)

print('=== 该区域的 UI 字符串（%d 条）===' % len(cands))
missing = []
for s in cands:
    ok = s in E or s in C
    if not ok:
        missing.append(s)
    print('  %s %s' % ('[有]' if ok else '[缺]', s))

print()
print('missing: %s' % missing)
json.dump(missing, open(os.path.join(WS, 'data', 'region_missing.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
