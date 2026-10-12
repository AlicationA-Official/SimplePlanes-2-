"""Scan assemblies for UTF-16LE text runs (covers strings kept outside the #US heap,
e.g. the rotating designer tips) and diff them against the dictionary."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

j = json.load(open(DICT, encoding='utf-8-sig'))
E = set(j['entries'])
C = {e['key'] for e in j['contextEntries']}
PRE = [p['sourcePrefix'] for p in j['dynamicPrefixEntries']]
SUF = [p['sourceSuffix'] for p in j['dynamicSuffixEntries']]

RUN = re.compile(rb'(?:[\x20-\x7e]\x00){8,}')
texts = set()
for dll in ('Game.dll', 'Jundroo.Common.dll', 'Jundroo.Packages.dll'):
    p = os.path.join(MANAGED, dll)
    if not os.path.exists(p):
        continue
    blob = open(p, 'rb').read()
    for m in RUN.finditer(blob):
        texts.add(m.group().decode('utf-16-le'))

print('UTF-16 runs collected: %d' % len(texts))


def covered(s):
    return (s in E or s in C
            or any(s.startswith(p) for p in PRE)
            or any(s.endswith(x) for x in SUF))


tips = sorted(t for t in texts if t.startswith('Tip: ') and not covered(t))
print()
print('=== 未翻译的 Tip（%d 条）===' % len(tips))
for t in tips:
    print('  ', t)

# other UI-ish sentences that look like tooltips/help text
def uiish(s):
    if len(s) < 25 or len(s) > 300:
        return False
    if not s[0].isupper() or ' ' not in s:
        return False
    if not s.endswith('.'):
        return False
    if covered(s):
        return False
    if re.search(r'[\x00-\x08\x0b-\x1f]', s):
        return False
    return True


others = sorted(t for t in texts if uiish(t))
print()
print('=== 其它疑似 UI 说明（%d 条，前 60 条）===' % len(others))
for t in others[:60]:
    print('  ', t[:150])

json.dump({'tips': tips, 'others': others},
          open(os.path.join(WS, 'data', 'utf16_gaps.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('written data/utf16_gaps.json')
