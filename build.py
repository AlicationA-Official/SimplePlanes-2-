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
    'gap_fill_bindprompt.json',
    'gap_fill_partprops.json',
    'gap_fill_parttips.json',
    'gap_fill_tutorial.json',
    'gap_fill_capture.json',
    'gap_fill_overload.json',
    'gap_fill_options.json',
]
CTX_FILE = 'gap_fill_context.json'
DYN_FILE = 'gap_fill_dynamic.json'
DYN_SUFFIX_FILE = 'gap_fill_dynamic_suffix.json'
PARTPREFIX_FILE = 'gap_fill_partname_prefix.json'
REMOVALS_FILE = 'removals.json'
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

    # 注意顺序：插件取"第一个匹配"的前缀规则，所以零件名这类长前缀要排在通用前缀之前
    pre_base = list(base.get('dynamicPrefixEntries', []))
    seen_pre = {e.get('sourcePrefix') for e in pre_base}
    pre_added = []
    for name in (PARTPREFIX_FILE, DYN_FILE):
        for e in load(os.path.join(SRC, name), {}).get('dynamicPrefixEntries', []):
            if e.get('sourcePrefix') in seen_pre:
                continue
            seen_pre.add(e.get('sourcePrefix'))
            pre_added.append(e)
    merged['dynamicPrefixEntries'] = pre_base + pre_added

    dyn_suffix = load(os.path.join(SRC, DYN_SUFFIX_FILE), {})
    suf_base = list(base.get('dynamicSuffixEntries', []))
    seen_suf = {e.get('sourceSuffix') for e in suf_base}
    suf_added = [e for e in dyn_suffix.get('dynamicSuffixEntries', [])
                 if e.get('sourceSuffix') not in seen_suf]
    merged['dynamicSuffixEntries'] = suf_base + suf_added

    # 游戏会拿控件的“显示文本”做逻辑比较的字符串，翻译后会破坏功能，必须移除
    removals = load(os.path.join(SRC, REMOVALS_FILE), [])
    removed = [k for k in removals if k in merged['entries']]
    for k in removed:
        del merged['entries'][k]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8-sig' if has_bom else 'utf-8', newline='\n') as f:
        f.write(json.dumps(merged, ensure_ascii=False, indent=2))

    total = (len(merged['entries']) + len(merged['contextEntries'])
             + len(merged.get('dynamicSuffixEntries', [])) + len(merged.get('dynamicPrefixEntries', [])))
    print('baseline entries      : %d' % len(entries))
    print('added entries         : %d' % len(added))
    print('added context entries : %d' % len(ctx_added))
    print('added prefix rules    : %d' % len(pre_added))
    print('added suffix rules    : %d' % len(suf_added))
    print('removed (text-compared): %d %s' % (len(removed), removed))
    print('skipped (already there): %d' % len(dup))
    print('skipped (in context)   : %d %s' % (len(in_ctx), in_ctx))
    print('---')
    print('entries               : %d' % len(merged['entries']))
    print('contextEntries        : %d' % len(merged['contextEntries']))
    print('dynamicPrefixEntries  : %d' % len(merged['dynamicPrefixEntries']))
    print('dynamicSuffixEntries  : %d' % len(merged['dynamicSuffixEntries']))
    print('total loadable        : %d' % total)
    print('written               : %s' % args.out)


if __name__ == '__main__':
    main()
