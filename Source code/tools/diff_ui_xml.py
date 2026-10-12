"""Compare data-driven UI XML text against the localization plugin dictionary."""
import glob
import html
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT = os.path.join(WS, 'dl', 'localization', 'zh-CN.json')

ATTR = re.compile(r'(text|tooltip|title|label|placeholder|description|displayName)\s*=\s*"([^"]*)"')


def decode(s):
    return html.unescape(s).replace('\\n', '\n')


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    keys = set(j['entries'].keys()) | set(e['key'] for e in j['contextEntries'])

    docs = {}
    all_values = set()
    for f in sorted(glob.glob(os.path.join(WS, 'data', 'ui_xml', '*.xml'))):
        blob = open(f, 'rb').read()
        try:
            text = blob.decode('utf-8')
        except UnicodeDecodeError:
            text = blob.decode('latin1')
        values = {decode(v) for _, v in ATTR.findall(text)}
        values = {v for v in values if v.strip() and re.search(r'[A-Za-z]', v)}
        docs[f] = values
        all_values |= values

    missing = sorted(all_values - keys)
    print('data-driven UI strings (unique): %d' % len(all_values))
    print('already in plugin dictionary   : %d' % len(all_values & keys))
    print('missing                        : %d' % len(missing))
    print()

    for f, values in docs.items():
        if 'BUILD' in values or 'FLY' in values:
            miss = sorted(values - keys)
            print('=== main-menu doc: %s  (%d strings, %d missing) ==='
                  % (os.path.basename(f), len(values), len(miss)))
            for v in sorted(values):
                print('   %s %s' % ('[缺]' if v not in keys else '[有]', v[:72].replace('\n', ' / ')))
            print()

    out = os.path.join(WS, 'data', 'ui_xml_missing.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(missing))
    print('full missing list -> %s' % out)

    print()
    print('=== all missing data-driven UI strings ===')
    for v in missing:
        print('   %s' % v[:90].replace('\n', ' / '))


if __name__ == '__main__':
    main()
