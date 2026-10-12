#!/usr/bin/env python3
"""SimplePlanes 2 汉化词表构建脚本（自包含，无需其它依赖）

用法：
    python build.py                # 输出到 build/zh-CN.json
    python build.py --out out.json

输入：
    base/zh-CN.json    原插件 v0.1.6 词表（基线，不要改）
    src/*.json         本补丁新增的词条 / 上下文规则 / 动态规则
输出：
    build/zh-CN.json   可直接放进插件目录的合并词表

合并规则（与插件的查表顺序一致）：
    1. 原词表已有同名键 -> 跳过（保留原作者译文）
    2. 键已存在 contextEntries -> 默认跳过（避免破坏"同词不同义"），
       除非列在 src/allow_context_dupes.json 中
    3. 其余写入 entries / contextEntries / dynamicPrefixEntries
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'base', 'zh-CN.json')
SRC = os.path.join(HERE, 'src')
ENTRY_FILES = [
    'gap_fill_entries.json',
    'gap_fill_entries2.json',
    'gap_fill_entries3.json',
    'gap_fill_entries4.json',
    'gap_fill_shortcuts.json',
    'gap_fill_parts.json',
]
CTX_FILE = 'gap_fill_context.json'
DYN_FILE = 'gap_fill_dynamic.json'
ALLOW_FILE = 'allow_context_dupes.json'


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'build', 'zh-CN.json'))
    args = ap.parse_args()

    if not os.path.exists(BASE):
        sys.exit('缺少基线词表：%s' % BASE)

    raw = open(BASE, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')          # 原词表带 BOM，输出保持一致
    base = json.loads(raw.decode('utf-8-sig'))

    entries = base['entries']
    ctx_keys = {e['key'] for e in base.get('contextEntries', [])}
    allow = set(load(os.path.join(SRC, ALLOW_FILE), []))

    added, dup, in_ctx = {}, [], []
    for name in ENTRY_FILES:
        for k, v in load(os.path.join(SRC, name), {}).items():
            if k in entries or k in added:
                dup.append(k)
                continue
            if k in ctx_keys and k not in allow:
                in_ctx.append(k)
                continue
            added[k] = v

    merged = dict(base)
    merged['entries'] = dict(list(entries.items()) + sorted(added.items()))

    ctx_base = list(base.get('contextEntries', []))
    seen = {(e.get('key'), e.get('sceneName'), e.get('gameObjectPathContains')) for e in ctx_base}
    ctx_added = []
    for e in load(os.path.join(SRC, CTX_FILE), []):
        sig = (e.get('key'), e.get('sceneName'), e.get('gameObjectPathContains'))
        if sig not in seen:
            seen.add(sig)
            ctx_added.append(e)
    merged['contextEntries'] = ctx_base + ctx_added

    dyn = load(os.path.join(SRC, DYN_FILE), {})
    pre_base = list(base.get('dynamicPrefixEntries', []))
    seen_pre = {e.get('sourcePrefix') for e in pre_base}
    pre_added = [e for e in dyn.get('dynamicPrefixEntries', []) if e.get('sourcePrefix') not in seen_pre]
    merged['dynamicPrefixEntries'] = pre_base + pre_added

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8-sig' if has_bom else 'utf-8', newline='\n') as f:
        f.write(json.dumps(merged, ensure_ascii=False, indent=2))

    total = (len(merged['entries']) + len(merged['contextEntries'])
             + len(merged.get('dynamicSuffixEntries', [])) + len(merged.get('dynamicPrefixEntries', [])))
    print('baseline entries      : %d' % len(entries))
    print('added entries         : %d' % len(added))
    print('added context entries : %d' % len(ctx_added))
    print('added prefix rules    : %d' % len(pre_added))
    print('skipped (already there): %d' % len(dup))
    print('skipped (in context)   : %d %s' % (len(in_ctx), in_ctx))
    print('---')
    print('entries               : %d' % len(merged['entries']))
    print('contextEntries        : %d' % len(merged['contextEntries']))
    print('dynamicPrefixEntries  : %d' % len(merged['dynamicPrefixEntries']))
    print('dynamicSuffixEntries  : %d' % len(merged.get('dynamicSuffixEntries', [])))
    print('total loadable        : %d' % total)
    print('written               : %s' % args.out)


if __name__ == '__main__':
    main()
