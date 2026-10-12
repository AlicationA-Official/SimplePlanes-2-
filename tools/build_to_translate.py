"""Build the final, safe-to-key list of missing UI strings.

Rules
  * multi-line strings (contain \\n) are dropped: the game injects the rendered
    key glyph / shortcut text at runtime, so the XML form would not match.
  * strings containing [Placeholder] tokens are dropped for the same reason.
  * strings already present in the plugin's entries or contextEntries are dropped.
  * credits (person names / callsigns) are dropped.
  * expression / binding / single-character tokens are dropped.
"""
import glob
import html
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT = os.path.join(WS, 'dl', 'localization', 'zh-CN.json')
GAME = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2'

ATTR = re.compile(r'(text|tooltip|title|label|placeholder|description|displayName)\s*=\s*"([^"]*)"')

# from the credits screen: <Instance templateId="credit" name="..." />
CREDIT = re.compile(r'name="([^"]*)"')

SKIP_EXACT = {'Mostly', 'C', 'A', 'B', 'R', 'G', 'OUT', 'Suit', 'Temp', 'TEMP', 'Test 23',
              'The Big L', 'Zero', 'NEW', 'OLD', 'α {-craft.AngleOfAttack;#0.0}'}


def decode(s):
    return html.unescape(s)


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    known = set(j['entries'].keys()) | set(e['key'] for e in j['contextEntries'])

    xml_strings = set()
    for f in sorted(glob.glob(os.path.join(WS, 'data', 'ui_xml', '*.xml'))):
        blob = open(f, 'rb').read()
        try:
            text = blob.decode('utf-8')
        except UnicodeDecodeError:
            text = blob.decode('latin1')
        for _, v in ATTR.findall(text):
            xml_strings.add(decode(v))

    # runtime strings captured by the TMP probe
    runtime = set()
    harvest = os.path.join(GAME, 'BepInEx', 'sp2_harvest.txt')
    if os.path.exists(harvest):
        runtime = set(open(harvest, encoding='utf-8').read().split('\n'))

    candidates = xml_strings | runtime

    safe, dropped = [], {'multiline': 0, 'placeholder': 0, 'known': 0, 'token': 0, 'explicit': 0}
    for s in candidates:
        if not s.strip() or not re.search(r'[A-Za-z]', s):
            continue
        if s in known:
            dropped['known'] += 1
            continue
        if s in SKIP_EXACT:
            dropped['explicit'] += 1
            continue
        if '\n' in s or '\r' in s or '\\n' in s:
            dropped['multiline'] += 1
            continue
        if re.search(r'\[[A-Za-z]+\]', s):
            dropped['placeholder'] += 1
            continue
        if re.search(r'\{(?!\d)', s) or ';000' in s:
            dropped['placeholder'] += 1
            continue
        if s.startswith('@') or len(s.strip()) <= 2:
            dropped['token'] += 1
            continue
        if re.match(r'^[A-Za-z0-9_]+$', s) and not s.isalpha():
            dropped['token'] += 1
            continue
        safe.append(s)

    safe.sort(key=lambda x: (len(x), x))
    out = os.path.join(WS, 'data', 'to_translate.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(safe))
    print('dropped: %s' % dropped)
    print('safe-to-key missing strings: %d  -> %s' % (len(safe), out))
    for s in safe:
        print('   ' + s[:110])


if __name__ == '__main__':
    main()
