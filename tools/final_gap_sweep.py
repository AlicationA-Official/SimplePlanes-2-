"""Full sweep: every .NET user string (UTF-16) in the Jundroo assemblies that is
still missing from the dictionary."""
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
PRE = [p['sourcePrefix'] for p in j['dynamicPrefixEntries']]
SUF = [p['sourceSuffix'] for p in j['dynamicSuffixEntries']]

SKIP_WORDS = ('Prefab', 'Shader', 'Material', 'Asset', 'Guid', 'Texture', 'Mesh',
              'MonoBehaviour', 'ScriptableObject', 'UnityEngine', 'System.', 'Xml/',
              'http', '.dll', '.xml', '.json', 'Assets/', 'Sprites/')
PLACEHOLDER = re.compile(r'\{\d')


def interesting(s):
    if len(s) < 3 or len(s) > 240:
        return False
    if not re.search(r'[A-Za-z]{2,}', s):
        return False
    if s.startswith(('Tip: ', 'Tips: ')):
        return True
    if any(w in s for w in SKIP_WORDS):
        return False
    if re.search(r'[{}]', s) and not PLACEHOLDER.search(s):
        return False
    if '\\n' in s or '\n' in s or '\r' in s:
        return False
    if re.match(r'^[a-z]', s):                      # log messages start lowercase
        return False
    if re.search(r'[=<>|]', s):
        return False
    if re.match(r'^[A-Za-z0-9_./-]+$', s) and '_' in s:
        return False
    if re.match(r'^[A-Za-z]+$', s) and len(s) > 14 and re.search(r'[a-z][A-Z]', s):
        return False
    if ' ' not in s and len(s) < 4:
        return False
    return True


def covered(s):
    if s in E or s in C:
        return True
    if any(s.startswith(p) for p in PRE):
        return True
    if any(s.endswith(x) for x in SUF):
        return True
    return False


found = {}
for dll in ('Game.dll', 'Jundroo.Common.dll', 'Jundroo.Packages.dll'):
    path = os.path.join(MANAGED, dll)
    if not os.path.exists(path):
        continue
    m = Module(path)
    for s in m.user_strings():
        if not interesting(s) or covered(s):
            continue
        found.setdefault(s, dll)

print('still missing candidates: %d' % len(found))
out = os.path.join(WS, 'data', 'final_gap_sweep.txt')
with open(out, 'w', encoding='utf-8') as f:
    for s in sorted(found):
        f.write('%s\t%s\n' % (found[s], s))
print('written %s' % out)
print()
for s in sorted(found):
    print('  [%s] %s' % (found[s][:16], s[:110]))
