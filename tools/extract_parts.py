"""Extract every DesignerPart (name / category / description) from Unity assets
and diff against the current translation dictionary.

Keys used by the plugin:
    "<Name>"                      (part list label)
    "<Name>\n<Description>"       (tooltip / properties header)
"""
import glob
import html
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')

PART = re.compile(
    rb'<DesignerPart\s+([^>]*?)>',
    re.S,
)
ATTR = re.compile(r'(\w+)\s*=\s*"([^"]*)"')


def attrs_of(raw):
    text = raw.decode('utf-8', 'replace')
    return {k: html.unescape(v) for k, v in ATTR.findall(text)}


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    known = set(j['entries'].keys()) | set(e['key'] for e in j['contextEntries'])

    parts = {}
    files = [os.path.join(ASSETS_DIR, 'resources.assets'),
             os.path.join(ASSETS_DIR, 'level3'),
             os.path.join(ASSETS_DIR, 'level5')]
    for path in files:
        if not os.path.exists(path):
            continue
        blob = open(path, 'rb').read()
        for m in PART.finditer(blob):
            a = attrs_of(m.group(1))
            name = a.get('name')
            if not name:
                continue
            desc = a.get('description', '')
            cat = a.get('category', '')
            parts.setdefault(name, {'description': desc, 'category': cat})

    print('DesignerPart entries found : %d' % len(parts))

    missing_name, missing_desc, have = [], [], 0
    for name, info in sorted(parts.items()):
        combo = name + '\n' + info['description'] if info['description'] else name
        name_ok = name in known
        combo_ok = combo in known
        if name_ok and combo_ok:
            have += 1
        else:
            if not name_ok:
                missing_name.append(name)
            if not combo_ok:
                missing_desc.append((name, info['description'], info['category']))

    print('fully translated           : %d' % have)
    print('missing bare name          : %d' % len(missing_name))
    print('missing name+description   : %d' % len(missing_desc))
    print()

    cats = sorted({i['category'] for i in parts.values() if i['category']})
    miss_cats = [c for c in cats if c not in known]
    print('categories total %d, untranslated %d: %s' % (len(cats), len(miss_cats), miss_cats))

    out = os.path.join(WS, 'data', 'parts_to_translate.json')
    payload = [{'name': n, 'description': d, 'category': c} for n, d, c in missing_desc]
    json.dump(payload, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print()
    print('untranslated parts -> %s' % out)
    for n, d, c in missing_desc:
        print('  [%s] %s' % (c, n))
        if d:
            print('        %s' % d[:150])


if __name__ == '__main__':
    main()
