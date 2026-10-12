"""Build the gap-fill patch: merge all translation additions into the v0.1.6 dictionary.

Sources (all optional except the base dictionary)
  patch/gap_fill_entries.json     UI text round 1
  patch/gap_fill_entries2.json    UI text round 2
  patch/gap_fill_entries3.json    controls / settings tooltips / tips
  patch/gap_fill_shortcuts.json   '<label>\\nShortcut: [not set]' variants
  patch/gap_fill_parts.json       designer part names + descriptions
  patch/gap_fill_context.json     context (scene + widget path) rules
  patch/gap_fill_dynamic.json     dynamic prefix rules for [keybinding] tooltips
  patch/allow_context_dupes.json  keys allowed in both context and plain entries

Outputs
  patch/zh-CN.json                merged dictionary, ready to drop into the game
  patch/fragments/9x-*.json       upstream-style fragments
"""
import json
import os

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(WS, 'dl', 'localization', 'zh-CN.json')
ENTRY_FILES = ['gap_fill_entries.json', 'gap_fill_entries2.json', 'gap_fill_entries3.json',
               'gap_fill_entries4.json', 'gap_fill_shortcuts.json', 'gap_fill_parts.json']
CTX_FILE = 'gap_fill_context.json'
DYN_FILE = 'gap_fill_dynamic.json'
ALLOW_FILE = 'allow_context_dupes.json'
OUT_JSON = os.path.join(WS, 'patch', 'zh-CN.json')
FRAG_DIR = os.path.join(WS, 'patch', 'fragments')


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def main():
    raw = open(BASE, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    base = json.loads(raw.decode('utf-8-sig'))

    entries = base['entries']
    ctx_keys = {e['key'] for e in base.get('contextEntries', [])}
    allow = set(load(os.path.join(WS, 'patch', ALLOW_FILE), []))

    added = {}
    skipped_dup, skipped_ctx = [], []
    for name in ENTRY_FILES:
        data = load(os.path.join(WS, 'patch', name), {})
        for k, v in data.items():
            if k in entries or k in added:
                skipped_dup.append(k)
                continue
            if k in ctx_keys and k not in allow:
                skipped_ctx.append(k)
                continue
            added[k] = v

    merged = dict(base)
    merged['entries'] = dict(list(entries.items()) + sorted(added.items()))

    # context entries
    ctx_base = list(base.get('contextEntries', []))
    seen_ctx = {(e.get('key'), e.get('sceneName'), e.get('gameObjectPathContains')) for e in ctx_base}
    ctx_added = []
    for e in load(os.path.join(WS, 'patch', CTX_FILE), []):
        sig = (e.get('key'), e.get('sceneName'), e.get('gameObjectPathContains'))
        if sig in seen_ctx:
            continue
        seen_ctx.add(sig)
        ctx_added.append(e)
    merged['contextEntries'] = ctx_base + ctx_added

    # dynamic prefix rules
    dyn = load(os.path.join(WS, 'patch', DYN_FILE), {})
    pre_base = list(base.get('dynamicPrefixEntries', []))
    seen_pre = {e.get('sourcePrefix') for e in pre_base}
    pre_added = [e for e in dyn.get('dynamicPrefixEntries', []) if e.get('sourcePrefix') not in seen_pre]
    merged['dynamicPrefixEntries'] = pre_base + pre_added

    os.makedirs(FRAG_DIR, exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8-sig' if has_bom else 'utf-8', newline='\n') as f:
        f.write(json.dumps(merged, ensure_ascii=False, indent=2))

    for name in ENTRY_FILES:
        data = load(os.path.join(WS, 'patch', name), {})
        page = name.replace('gap_fill_', '').replace('.json', '')
        frag = {'page': '9x-' + page,
                'entries': [{'key': k, 'value': v} for k, v in sorted(data.items())]}
        with open(os.path.join(FRAG_DIR, '9x-%s.json' % page), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(frag, f, ensure_ascii=False, indent=2)

    if ctx_added:
        with open(os.path.join(FRAG_DIR, '9x-context.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'page': '9x-context', 'contextEntries': ctx_added}, f, ensure_ascii=False, indent=2)
    if pre_added:
        with open(os.path.join(FRAG_DIR, '9x-dynamic-prefix.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'page': '9x-dynamic-prefix', 'dynamicPrefixEntries': pre_added}, f,
                      ensure_ascii=False, indent=2)

    total = (len(merged['entries']) + len(merged['contextEntries'])
             + len(merged.get('dynamicSuffixEntries', [])) + len(merged.get('dynamicPrefixEntries', [])))
    print('base entries          : %d' % len(entries))
    print('added entries         : %d' % len(added))
    print('added context entries : %d' % len(ctx_added))
    print('added prefix rules    : %d' % len(pre_added))
    print('skipped (dup entries) : %d' % len(skipped_dup))
    print('skipped (in context)  : %d %s' % (len(skipped_ctx), skipped_ctx))
    print('---')
    print('entries               : %d' % len(merged['entries']))
    print('contextEntries        : %d' % len(merged['contextEntries']))
    print('dynamicPrefixEntries  : %d' % len(merged['dynamicPrefixEntries']))
    print('total loadable        : %d' % total)
    print('written               : %s' % OUT_JSON)


if __name__ == '__main__':
    main()
