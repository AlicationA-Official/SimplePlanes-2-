"""Check which part-list headers are missing from the dictionary."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

blob = open(ASSETS, 'rb').read()
headers = sorted({m.decode() for m in re.findall(rb'header="([^"]+)"', blob)})

j = json.load(open(DICT, encoding='utf-8-sig'))
entries = set(j['entries'])
ctx = {}
for e in j['contextEntries']:
    ctx.setdefault(e['key'], []).append((e.get('sceneName'), e.get('gameObjectPathContains')))

print('headers total: %d' % len(headers))
miss = []
for h in headers:
    if h in entries:
        state = 'entries -> %s' % j['entries'][h][:24]
    elif h in ctx:
        state = 'context %s' % (ctx[h],)
    else:
        state = '*** MISSING ***'
        miss.append(h)
    print('   %-24s %s' % (h, state))

print()
print('missing headers (%d): %s' % (len(miss), miss))
json.dump(miss, open(os.path.join(WS, 'data', 'headers_missing.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
