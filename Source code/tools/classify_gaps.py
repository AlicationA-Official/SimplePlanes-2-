"""Classify missing data-driven UI strings into translate / review / skip buckets."""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT = os.path.join(WS, 'dl', 'localization', 'zh-CN.json')

SKIP_EXACT = {
    'Mostly', 'C', 'A', 'B', 'R', 'G',
}


def load_keys():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    keys = set(j['entries'].keys()) | set(e['key'] for e in j['contextEntries'])
    return keys


def classify(s):
    if s in SKIP_EXACT:
        return 'skip'
    if s.startswith('@'):
        return 'skip'
    if re.match(r'^[A-Z]{2,5}\s*\{', s):
        return 'skip'
    if '{craft.' in s or ';000' in s or ';00000' in s:
        return 'skip'
    if len(s.strip()) <= 2:
        return 'skip'
    if re.match(r'^[A-Za-z0-9_]+$', s) and not s.isalpha():
        return 'skip'
    if re.match(r'^[A-Za-z]+$', s):
        # single token: mostly IDs / key names / proper nouns -> review
        return 'review'
    return 'translate'


def main():
    keys = load_keys()
    missing = open(os.path.join(WS, 'data', 'ui_xml_missing.txt'), encoding='utf-8').read().splitlines()
    buckets = {'translate': [], 'review': [], 'skip': []}
    for s in missing:
        buckets[classify(s)].append(s)

    for name in ('translate', 'review', 'skip'):
        items = buckets[name]
        print('### %s: %d' % (name, len(items)))
        if name != 'skip':
            for s in items:
                print('   ' + s.replace('\n', ' / ')[:120])
        print()

    for name in ('translate', 'review', 'skip'):
        open(os.path.join(WS, 'data', 'bucket_%s.txt' % name), 'w', encoding='utf-8').write(
            '\n'.join(buckets[name]))


if __name__ == '__main__':
    main()
