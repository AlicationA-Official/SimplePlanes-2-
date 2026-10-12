"""Extract every control-binding display name from the Rewired data and diff
against the dictionary; also list UI tooltips that contain [Placeholder] tokens."""
import glob
import html
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

j = json.load(open(DICT, encoding='utf-8-sig'))
entries = set(j['entries'])
ctx_keys = {e['key'] for e in j['contextEntries']}

blob = open(ASSETS, 'rb').read()
idx = blob.find(b'Damage Visualizer')
window = blob[idx - 30000: idx + 200000]

runs = re.findall(rb'[\x20-\x7e]{3,60}', window)
cands = set()
for r in runs:
    s = r.decode('latin1').strip()
    if not s or len(s) > 48:
        continue
    if not re.match(r'^[A-Za-z][A-Za-z0-9 /+().,\'-]*$', s):
        continue
    if ' ' not in s and re.search(r'[A-Z]', s[1:]):
        continue          # CamelCase internal name
    if ' ' not in s and len(s) > 12:
        continue
    cands.add(s)

# keep only ones that look like real action labels (present in the action map region)
missing_input = sorted(s for s in cands if s not in entries and s not in ctx_keys)
print('=== 输入动作候选 %d 个，其中未翻译 %d 个 ===' % (len(cands), len(missing_input)))
for s in missing_input:
    print('   ', s)

# --- tooltips with [Placeholder] tokens -------------------------------------
print()
print('=== UI tooltip 中含 [占位符] 的条目 ===')
seen = set()
for f in sorted(glob.glob(os.path.join(WS, 'data', 'ui_xml', '*.xml'))):
    t = open(f, 'rb').read().decode('utf-8', 'replace')
    for m in re.finditer(r'tooltip="([^"]*)"', t):
        v = html.unescape(m.group(1))
        if '[' not in v:
            continue
        seen.add(v)
print('共 %d 条' % len(seen))
for v in sorted(seen):
    label = v.split('\n')[0]
    state = '有' if v in entries else ('前缀可覆盖' if label in entries else '缺')
    print('  [%s] %s' % (state, v.replace('\n', ' / ')[:110]))
