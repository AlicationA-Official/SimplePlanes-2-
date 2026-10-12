"""Targeted sweep of Game.dll user strings:
  A. all designer/loader tips ('Tip: ...')
  B. settings tooltips (full descriptive sentences used by the settings dialog)
Both are diffed against the current dictionary.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clrmeta import Module  # noqa: E402

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

j = json.load(open(DICT, encoding='utf-8-sig'))
E = set(j['entries'])
C = {e['key'] for e in j['contextEntries']}

VERB = re.compile(
    r'^(Adjusts|Toggles|Sets|Determines|Enables|Disables|Controls|Defines|Increases|Decreases|'
    r'Changes|Selects|Limits|Allows|Whether|How |When |The (number|interval|amount|maximum|minimum|'
    r'rate|size|speed|distance|quality|level|field|resolution|name|type|value|angle|scale|time)|'
    r'This setting|Higher|Lower|If |Used to|Specifies|Shows|Adds|Applies|Gives|Makes|Prevents|'
    r'Raises|Reduces|Scales|Enables or disables)')

tips, tooltips = set(), set()
for dll in ('Game.dll', 'Jundroo.Common.dll', 'Jundroo.Packages.dll'):
    p = os.path.join(MANAGED, dll)
    if not os.path.exists(p):
        continue
    for s in Module(p).user_strings():
        s = s.strip()
        if s.startswith('Tip: '):
            tips.add(s)
        elif 30 <= len(s) <= 320 and s.endswith('.') and ' ' in s and VERB.match(s):
            tooltips.add(s)

print('=== Tip 提示：共 %d 条，未翻译 %d 条 ===' % (len(tips), sum(1 for t in tips if t not in E)))
for t in sorted(tips):
    print('  %s %s' % ('[缺]' if t not in E else '[有]', t))
print()
missing_tt = sorted(t for t in tooltips if t not in E)
print('=== 设置说明句：共 %d 条，未翻译 %d 条 ===' % (len(tooltips), len(missing_tt)))
for t in missing_tt:
    print('  %s' % t[:170])

out = os.path.join(WS, 'data', 'tips_and_tooltips.json')
json.dump({'tips_missing': sorted(t for t in tips if t not in E),
           'tooltips_missing': missing_tt}, open(out, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('written %s' % out)
