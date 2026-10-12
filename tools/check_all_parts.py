"""Complete part inventory across every asset file, plus contexts for leftover strings."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data'
CAP = os.path.join(WS, 'dl', 'localization', 'captured-texts.json')

# 1) which asset files define DesignerParts?
print('=== DesignerPart definitions per asset file ===')
allp = set()
for dp, dn, fn in os.walk(DATA):
    for f in fn:
        p = os.path.join(dp, f)
        if os.path.getsize(p) > 1200 * 1024 * 1024:
            continue
        try:
            blob = open(p, 'rb').read()
        except OSError:
            continue
        names = re.findall(rb'<DesignerPart\s+name="([^"]*)"', blob)
        if names:
            print('  %-34s %d parts' % (os.path.relpath(p, DATA), len(names)))
            allp |= {n.decode('utf-8', 'replace') for n in names}
print('  unique DesignerPart names: %d' % len(allp))

j = json.load(open(os.path.join(WS, 'patch', 'zh-CN.json'), encoding='utf-8-sig'))
miss = sorted(n for n in allp if n not in j['entries'])
print('  parts still without a bare-name entry: %s' % miss)

# 2) contexts for the leftover strings
print()
print('=== capture contexts for leftover strings ===')
d = json.load(open(CAP, encoding='utf-8-sig'))
targets = {'Turboshaft', 'Gear Leg', 'Animator', 'New Property Name', 'New Property Value',
           'Undo complete', 'Undoing last step...', 'Name \u25b2',
           'Tip: You can clone parts by clicking and dragging them with the right mouse button.',
           'Tip: You can press CTRL+Z to undo and CTRL+Y to redo.', 'BUILD', 'FLY'}
for e in d:
    if e['Text'] in targets:
        print('  %r' % e['Text'])
        for c in e.get('Contexts', [])[:2]:
            print('      scene=%s path=%s' % (c.get('SceneName'), c.get('GameObjectPath')))
