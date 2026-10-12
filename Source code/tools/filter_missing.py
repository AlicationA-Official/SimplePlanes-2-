"""Filter the plugin's own missing-texts list down to genuine gaps."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
MISSING = os.path.join(WS, 'dl', 'localization', 'missing-texts.txt')

lines = [l.strip() for l in open(MISSING, encoding='utf-8') if l.strip()]
blob = open(ASSETS, 'rb').read()
credits = {m.group(1).decode('utf-8', 'replace')
           for m in re.finditer(rb'<Instance\s+templateId="credit"\s+name="([^"]*)"', blob)}


def is_cjk(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s))


cjk = [l for l in lines if is_cjk(l)]
en = [l for l in lines if not is_cjk(l)]
names = [l for l in en if l in credits]
other = sorted(l for l in en if l not in credits)

print('total lines        : %d' % len(lines))
print('chinese (self-echo): %d' % len(cjk))
print('english            : %d' % len(en))
print('  credits names    : %d' % len(names))
print('  genuine others   : %d' % len(other))
print()
for l in other:
    print('   %r' % l)
