"""扫描已抽取的 77 份 UI XML，列出所有"看起来是显示文案"但词表里没有的字符串。

覆盖：text="..."、placeholderText="..."、<Constant value="...">、label=... 等。
过滤掉颜色(@Color.../#RRGGBB)、资源路径、纯符号与纯数字。
"""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UIDIR = os.path.join(WS, 'data', 'ui_xml')
DICT = os.path.join(WS, 'patch', 'zh-CN.json')
OUT = os.path.join(WS, 'data', 'ui_xml_gaps.json')

ATTRS = re.compile(r'\b(?:text|placeholderText|label|title|tooltip|message|description)="([^"]*)"')
CONSTS = re.compile(r'<Constant\s+name="[^"]*"\s+value="([^"]*)"')


def is_display(s):
    if len(s) < 2 or len(s) > 300:
        return False
    if s.startswith('@') or s.startswith('#') or '/' in s or '\\' in s:
        return False
    if re.fullmatch(r'[\W_]+', s):
        return False
    if not re.search(r'[A-Za-z]', s):
        return False
    if re.fullmatch(r'(true|false|none|null)', s, re.I):
        return False
    return True


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    tr = set(j['entries']) | {e['key'] for e in j['contextEntries']}

    found, missing = {}, {}
    for name in sorted(os.listdir(UIDIR)):
        if not name.endswith('.xml'):
            continue
        raw = open(os.path.join(UIDIR, name), encoding='utf-8', errors='replace').read()
        for m in list(ATTRS.finditer(raw)) + list(CONSTS.finditer(raw)):
            s = m.group(1).strip()
            if not is_display(s):
                continue
            found.setdefault(s, set()).add(name)
            if s not in tr:
                missing.setdefault(s, set()).add(name)

    print('UI XML 中的显示文案: %d 条' % len(found))
    print('其中词表未覆盖: %d 条' % len(missing))
    json.dump({k: sorted(v) for k, v in sorted(missing.items())},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('written %s' % OUT)
    print()
    for s in sorted(missing):
        print('   %-58s %s' % (s[:56], ','.join(sorted(missing[s]))[:40]))


if __name__ == '__main__':
    main()
