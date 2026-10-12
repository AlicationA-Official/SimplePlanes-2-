"""Extract the tip sentences (stored as plain UTF-16 runs near each other) and
finalise the settings-tooltip gap list."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed\Game.dll'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

blob = open(GAME, 'rb').read()
j = json.load(open(DICT, encoding='utf-8-sig'))
E = set(j['entries'])

anchor = blob.find('wrench icon'.encode('utf-16-le'))
print('anchor at 0x%X' % anchor)

RUN = re.compile(rb'(?:[\x20-\x7e]\x00){12,}')
region = blob[anchor - 40000: anchor + 40000]
runs = [m.group().decode('utf-16-le') for m in RUN.finditer(region)]

tips = []
for r in runs:
    r = r.strip()
    if not r.endswith('.'):
        continue
    if not r[0].isupper():
        continue
    if len(r) < 20 or len(r) > 220:
        continue
    if re.search(r'(Prefab|Shader|Material|Asset|GameObject|\{0\}|Steam|http)', r):
        continue
    tips.append(r)

tips = sorted(set(tips))
missing = [t for t in tips if ('Tip: ' + t) not in E]
print()
print('=== 候选 Tip 句子 %d 条，其中未翻译 %d 条 ===' % (len(tips), len(missing)))
for t in tips:
    flag = '[缺]' if ('Tip: ' + t) not in E else '[有]'
    print('  %s %s' % (flag, t))

out = os.path.join(WS, 'data', 'tip_sentences.json')
json.dump({'all': tips, 'missing': missing}, open(out, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('written %s' % out)
