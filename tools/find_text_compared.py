"""找出所有被游戏"当作逻辑判断依据"的界面文本。

模式：IL 里出现
    callvirt TextWidget::get_Text
    ldstr    "<某个字符串>"
    call     String::op_Equality / op_Inequality
说明游戏在拿控件的**显示文本**做分支判断——这类字符串一旦被翻译，逻辑就会失效
（例如绑定冲突对话框里的 "Remove" / "Replace"）。

输出这些字符串里、当前词表已经翻译的那些。
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clrmeta import Module  # noqa: E402

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')


def us_pairs(m):
    """yield (offset, string) for the #US heap"""
    off, size = m.streams['#US']
    i = 1
    while i < size:
        b0 = m.data[off + i]
        if b0 & 0x80 == 0:
            ln, hl = b0, 1
        elif b0 & 0xC0 == 0x80:
            ln, hl = ((b0 & 0x3F) << 8) | m.data[off + i + 1], 2
        else:
            ln = ((b0 & 0x1F) << 24) | (m.data[off + i + 1] << 16) | \
                 (m.data[off + i + 2] << 8) | m.data[off + i + 3]
            hl = 4
        raw = m.data[off + i + hl:off + i + hl + ln]
        if len(raw) == ln and ln:
            try:
                s = raw[:-1].decode('utf-16le')
            except UnicodeDecodeError:
                s = None
            if s:
                yield i, s
        i += hl + ln


def gettext_tokens(m):
    toks = set()
    for i, mr in enumerate(m.memberrefs):
        if mr['name'] == 'get_Text':
            toks.add(0x0A000000 | (i + 1))
    for i, meth in enumerate(m.methods):
        if meth['name'] == 'get_Text':
            toks.add(0x06000000 | (i + 1))
    return toks


def eq_tokens(m):
    """String::op_Equality / op_Inequality 的 token"""
    toks = set()
    for i, mr in enumerate(m.memberrefs):
        if mr['name'] in ('op_Equality', 'op_Inequality') and mr['parent'].endswith('String'):
            toks.add(0x0A000000 | (i + 1))
    return toks


def main():
    dll = 'Game.dll'
    path = os.path.join(MANAGED, dll)
    m = Module(path)
    blob = m.data
    get_text = gettext_tokens(m)
    eq = eq_tokens(m)
    print('get_Text token 数: %d, op_Equality/Inequality token 数: %d' % (len(get_text), len(eq)))

    j = json.load(open(DICT, encoding='utf-8-sig'))
    translated = dict(j['entries'])
    for e in j['contextEntries']:
        translated.setdefault(e['key'], e['value'])

    hits = {}
    for offset, s in us_pairs(m):
        if s not in translated:
            continue
        token = 0x70000000 | offset
        needle = b'\x72' + struct.pack('<I', token)
        pos = blob.find(needle)
        while pos >= 0:
            window = blob[max(0, pos - 48):pos]
            has_get_text = any((op + struct.pack('<I', gt)) in window
                               for gt in get_text for op in (b'\x6f', b'\x28'))
            # 紧随 ldstr 之后必须出现字符串比较调用
            follow = blob[pos + 5:pos + 5 + 24]
            has_eq = any((op + struct.pack('<I', t)) in follow
                         for t in eq for op in (b'\x6f', b'\x28'))
            if has_get_text and has_eq:
                hits[s] = translated[s]
                break
            pos = blob.find(needle, pos + 1)

    print()
    print('=== 被游戏用作文本比较、且当前已被翻译的字符串（%d 条）===' % len(hits))
    for k, v in sorted(hits.items()):
        print('   %-42r -> %r' % (k, v))

    out = os.path.join(WS, 'data', 'text_compared_translated.json')
    json.dump(hits, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print()
    print('written %s' % out)


if __name__ == '__main__':
    main()
