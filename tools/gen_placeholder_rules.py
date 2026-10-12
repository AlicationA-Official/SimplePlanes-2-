"""Generate rules for tooltips of the form '<label[...]>\nShortcut: [Token]'.

For every such tooltip we emit
  * an entry for the unbound case   '<label>\nShortcut: [not set]'
  * a dynamic prefix rule           sourcePrefix='<label>\nShortcut: '
                                    valuePrefix ='<cn label>\n快捷键：'
so every key binding (bound or unbound) ends up translated.
"""
import glob
import html
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

j = json.load(open(DICT, encoding='utf-8-sig'))
entries = j['entries']

tooltips = set()


def norm(s):
    # XML stores literal backslash-n; the game turns it into a real newline at runtime
    return s.replace('\\n', '\n').replace('\\r', '\r')


for f in sorted(glob.glob(os.path.join(WS, 'data', 'ui_xml', '*.xml'))):
    t = open(f, 'rb').read().decode('utf-8', 'replace')
    tooltips |= {norm(html.unescape(m.group(1))) for m in re.finditer(r'tooltip="([^"]*)"', t)}

blob = open(ASSETS, 'rb').read()
for m in re.finditer(rb'tooltip="([^"]*)"', blob):
    try:
        tooltips.add(norm(html.unescape(m.group(1).decode('utf-8'))))
    except UnicodeDecodeError:
        pass

MARK = 'Shortcut: '
CNMARK = '快捷键：'

# labels the dictionary never translated (no bound-key variant to reverse-engineer)
MANUAL = {
    'Fire Weapon': '发射武器',
    'Parking Brake': '驻车制动',
    'Recenter view': '视角回正',
    'Show/hide part in the designer': '在设计器中显示/隐藏零件',
    'Weld the selected parts so they to move together in the designer. Does not make them rigid in flight.':
        '焊接所选零件，使它们在设计器中一起移动。不会让它们在飞行中变成刚体。',
}

# index the dictionary by the English head of every already-translated shortcut tooltip
by_head = {}
for k, v in entries.items():
    if MARK in k and CNMARK in v:
        head_k = k.partition(MARK)[0]
        by_head[head_k] = v.partition(CNMARK)[0]

proposals, unresolved = [], []
for tip in sorted(tooltips):
    if '[' not in tip or MARK not in tip:
        continue
    head, _, tail = tip.partition(MARK)
    cands = [head, head.rstrip('\n'), head.split('\n')[0]]
    cn = next((by_head[c] for c in cands if c in by_head), None)
    if cn is None:
        cn = next((entries[c] for c in cands if c in entries), None)
    if cn is None:
        for c in cands:
            if c in MANUAL:
                cn = MANUAL[c]
                break
    if cn is None:
        unresolved.append(tip)
        continue
    if not tail.strip().startswith('['):
        continue
    # keep the two-line layout even if the source entry lacked the trailing newline
    if not cn.endswith('\n'):
        cn += '\n'
    # in the unbound case the game keeps the literal brackets
    unbound = head + MARK + '[not set]'
    proposals.append({
        'tip': tip,
        'entry_key': unbound,
        'entry_value': cn + CNMARK + '[未设置]',
        'prefix_source': head + MARK,
        'prefix_value': cn + CNMARK,
    })

print('placeholder tooltips processed: %d' % len(proposals))
print('unresolved (need manual label translation): %d' % len(unresolved))
for t in unresolved:
    print('   %r' % t[:120])
print()
for p in proposals:
    print('  %s' % p['tip'].replace('\n', ' / ')[:100])
    print('      entry : %r -> %r' % (p['entry_key'][-40:], p['entry_value'][-30:]))
    print('      prefix: %r -> %r' % (p['prefix_source'][:40], p['prefix_value'][:30]))

out = os.path.join(WS, 'data', 'placeholder_rules.json')
json.dump(proposals, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# emit the two patch files
sh = os.path.join(WS, 'patch', 'gap_fill_shortcuts.json')
dy = os.path.join(WS, 'patch', 'gap_fill_dynamic.json')
shortcut_entries = {p['entry_key']: p['entry_value'] for p in proposals}
prefix_rules = [
    {'sourcePrefix': p['prefix_source'], 'valuePrefix': p['prefix_value'], 'valueSuffix': ''}
    for p in proposals
]
json.dump(shortcut_entries, open(sh, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({'dynamicPrefixEntries': prefix_rules}, open(dy, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print()
print('written %s (%d entries)' % (sh, len(shortcut_entries)))
print('written %s (%d prefix rules)' % (dy, len(prefix_rules)))
print('written %s' % out)
